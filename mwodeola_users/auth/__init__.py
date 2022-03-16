from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken


AUTH_HEADER_TYPES = api_settings.AUTH_HEADER_TYPES

if not isinstance(api_settings.AUTH_HEADER_TYPES, (list, tuple)):
    AUTH_HEADER_TYPES = (AUTH_HEADER_TYPES,)

AUTH_HEADER_TYPE_BYTES = set(
    h.encode(HTTP_HEADER_ENCODING)
    for h in AUTH_HEADER_TYPES
)


def get_raw_token(request):
    """
    Extracts an unvalidated JSON web token from the given "Authorization"
    header value.
    """
    auth_header = request.META.get(api_settings.AUTH_HEADER_NAME, None)
    if auth_header is None:
        return None

    auth_header = auth_header.encode()

    parts = auth_header.split()
    if len(parts) == 0:
        # Empty AUTHORIZATION header sent
        return None

    if parts[0] not in AUTH_HEADER_TYPE_BYTES:
        # Assume the header does not contain a JSON web token
        return None

    if len(parts) != 2:
        raise AuthenticationFailed(
            _('Authorization header must contain two space-delimited values'),
            code='bad_authorization_header',
        )

    return parts[1].decode()


def get_user_from_request_token(request):
    raw_token = get_raw_token(request)
    validated_token = UntypedToken(raw_token)

    """
    Attempts to find and return a user using the given validated token.
    """
    try:
        user_id = validated_token[api_settings.USER_ID_CLAIM]
    except KeyError:
        raise InvalidToken(_('Token contained no recognizable user identification'))

    try:
        user = get_user_model().objects.get(**{api_settings.USER_ID_FIELD: user_id})
    except get_user_model().DoesNotExist:
        raise AuthenticationFailed(_('User not found'), code='user_not_found')

    if not user.is_active:
        raise AuthenticationFailed(_('User is inactive'), code='user_inactive')

    if user.is_locked:
        raise AuthenticationFailed(_('User is locked'), code='user_locked')

    return user
