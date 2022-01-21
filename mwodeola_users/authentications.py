from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthenticationForRefresh(JWTAuthentication):
    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []

        try:
            return RefreshToken(raw_token)
        except TokenError as e:
            messages.append({'token_class': RefreshToken.__name__,
                             'token_type': RefreshToken.token_type,
                             'message': e.args[0]})

        raise InvalidToken({
            'detail': _('Given token not valid for any token type'),
            'messages': messages,
        })
