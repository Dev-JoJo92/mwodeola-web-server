from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from ..models import MwodeolaUser


AUTH_LIMIT_DEFAULT = 5
AUTH_LIMIT = getattr(settings, "AUTH_LIMIT", AUTH_LIMIT_DEFAULT)


class UserAuthMixin:

    def get_user_by_authentication_rule(self, phone_number, password):
        user = None

        try:
            user = MwodeolaUser.objects.get(phone_number=phone_number)
        except ObjectDoesNotExist as e:
            pass

        if user is None:
            self.err_messages['detail'] = 'User not found'
            self.err_messages['code'] = 'user_not_found'
            self.err_status = status.HTTP_401_UNAUTHORIZED
            return None
        if self._is_locked_user(user):
            return None
        if self._is_inactive_user(user):
            return None

        result = authenticate(phone_number=phone_number, password=password)

        if result is None:
            if user.count_auth_failed < AUTH_LIMIT - 1:
                user.count_auth_failed += 1
                user.save()
                self.err_messages['detail'] = 'Authentication failed'
                self.err_messages['code'] = 'authentication_failed'
                self.err_messages['count'] = user.count_auth_failed
                self.err_messages['limit'] = AUTH_LIMIT
                self.err_status = status.HTTP_401_UNAUTHORIZED
            else:
                user.count_auth_failed += 1
                user.is_locked = True
                user.save()
                self._blacklist_all(user)
                self.err_messages['detail'] = 'Exceeded number of authentications'
                self.err_messages['code'] = 'authentication_exceed'
                self.err_status = status.HTTP_403_FORBIDDEN
            return None

        user.count_auth_failed = 0
        user.save()
        return user

    def get_user_for_inactive_user(self, phone_number, password):
        user = None

        try:
            user = MwodeolaUser.objects.get(phone_number=phone_number)
        except ObjectDoesNotExist as e:
            pass

        if user is None:
            self.err_messages['detail'] = 'User not found'
            self.err_messages['code'] = 'user_not_found'
            self.err_status = status.HTTP_401_UNAUTHORIZED
            return None
        if self._is_locked_user(user):
            return None

        authed_user = authenticate(phone_number=phone_number, password=password)

        if authed_user is None:
            if user.count_auth_failed < AUTH_LIMIT - 1:
                user.count_auth_failed += 1
                user.save()
                self.err_messages['detail'] = 'Authentication failed'
                self.err_messages['code'] = 'authentication_failed'
                self.err_messages['count'] = user.count_auth_failed
                self.err_messages['limit'] = AUTH_LIMIT
                self.err_status = status.HTTP_401_UNAUTHORIZED
            else:
                user.count_auth_failed += 1
                user.is_locked = True
                user.save()
                self._blacklist_all(user)
                self.err_messages['detail'] = 'Exceeded number of authentications'
                self.err_messages['code'] = 'authentication_exceed'
                self.err_status = status.HTTP_403_FORBIDDEN
            return None

        user.count_auth_failed = 0
        user.save()
        return user

    def get_user_for_locked_user(self, phone_number, password):
        user = None

        try:
            user = MwodeolaUser.objects.get(phone_number=phone_number)
        except ObjectDoesNotExist as e:
            pass

        if user is None:
            self.err_messages['detail'] = 'User not found'
            self.err_messages['code'] = 'user_not_found'
            self.err_status = status.HTTP_401_UNAUTHORIZED
            return None

        authed_user = authenticate(phone_number=phone_number, password=password)

        if authed_user is None:
            if user.count_auth_failed < AUTH_LIMIT - 1:
                user.count_auth_failed += 1
                user.save()
                self.err_messages['detail'] = 'Authentication failed'
                self.err_messages['code'] = 'authentication_failed'
                self.err_messages['count'] = user.count_auth_failed
                self.err_messages['limit'] = AUTH_LIMIT
                self.err_status = status.HTTP_401_UNAUTHORIZED
            else:
                user.count_auth_failed += 1
                user.is_locked = True
                user.save()
                self._blacklist_all(user)
                self.err_messages['detail'] = 'Exceeded number of authentications'
                self.err_messages['code'] = 'authentication_exceed'
                self.err_status = status.HTTP_403_FORBIDDEN
            return None

        user.count_auth_failed = 0
        user.save()
        return user

    def _is_locked_user(self, user) -> bool:
        if user.is_locked:
            self.err_messages['detail'] = 'User is locked'
            self.err_messages['code'] = 'user_locked'
            self.err_status = status.HTTP_403_FORBIDDEN
            return True
        else:
            return False

    def _is_inactive_user(self, user) -> bool:
        if not user.is_active:
            self.err_messages['detail'] = 'User is inactive'
            self.err_messages['code'] = 'user_inactive'
            self.err_status = status.HTTP_403_FORBIDDEN
            return True
        else:
            return False

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
