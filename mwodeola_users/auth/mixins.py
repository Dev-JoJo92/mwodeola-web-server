from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from ..models import MwodeolaUser


class UserAuthMixin:

    def get_user_by_authentication_rule(self, phone_number, password):
        user = None

        try:
            user = MwodeolaUser.objects.get(phone_number=phone_number)
        except ObjectDoesNotExist as e:
            pass

        if user is None:
            self.err_messages['error'] = 'not our member'
            self.err_status = status.HTTP_401_UNAUTHORIZED
            return None
        if not user.is_active:
            self.err_messages['error'] = 'dormant account'
            self.err_status = status.HTTP_403_FORBIDDEN
            return None
        if user.is_locked:
            self.err_messages['error'] = 'locked account'
            self.err_status = status.HTTP_403_FORBIDDEN
            return None

        result = authenticate(phone_number=phone_number, password=password)

        if result is None:
            if user.count_auth_failed < 4:
                user.count_auth_failed += 1
                user.save()
                self.err_messages['error'] = f'authentication failed(count={user.count_auth_failed})'
                self.err_status = status.HTTP_401_UNAUTHORIZED
            else:
                user.is_locked = True
                user.save()
                self._blacklist_all(user)
                self.err_messages['error'] = 'Exceeded number of authentications'
                self.err_status = status.HTTP_403_FORBIDDEN
            return None

        user.count_auth_failed = 0
        user.save()
        return user

    # 성능 이슈
    def _blacklist_all(self, user):
        tokens = OutstandingToken.objects.filter(user_id=user.id)
        # print(f'tokens.len={len(tokens)}')
        for token in tokens:
            try:
                # print(f'tokens={token.id}')
                BlacklistedToken.objects.get(token_id=token.id)
            except ObjectDoesNotExist:
                # print(f'tokens={token.id} 블랙리스트!!')
                RefreshToken(token.token).blacklist()
                continue
