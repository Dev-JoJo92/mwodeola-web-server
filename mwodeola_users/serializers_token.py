from abc import abstractmethod

from django.contrib import auth
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.exceptions import TokenError

from .auth.mixins import UserAuthMixin

if api_settings.BLACKLIST_AFTER_ROTATION:
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(*args, **kwargs)


class BaseTokenSerializer(serializers.Serializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_401_UNAUTHORIZED

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages['detail'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['errors'] = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        return True

    def create(self, validated_data):
        return {}

    def update(self, instance, validated_data):
        return {}


class TokenObtainPairSerializer(UserAuthMixin, BaseTokenSerializer):
    phone_number = serializers.CharField(max_length=16)
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(False):
            return False

        phone_number = self.validated_data['phone_number']
        password = self.validated_data['password']

        user = self.get_user_by_authentication_rule(phone_number, password)
        if user is None:
            return False

        refresh = self.get_token(user)

        self.results['refresh'] = str(refresh)
        self.results['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return True

    @classmethod
    def get_token(cls, user):
        cls.blacklist_last_token(user)
        return RefreshToken.for_user(user)

    @classmethod
    def blacklist_last_token(cls, user):
        user_id = user.pk
        try:
            latest_token_queryset = OutstandingToken.objects \
                .filter(user_id=user_id) \
                .latest('id')

            is_blacklist = BlacklistedToken.objects \
                .filter(token_id=latest_token_queryset.id) \
                .exists()

            if not is_blacklist:
                RefreshToken(latest_token_queryset.token).blacklist()

        except (ObjectDoesNotExist, TokenError):
            pass


class TokenRefreshSerializer(BaseTokenSerializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(False):
            return False

        refresh = RefreshToken(self.validated_data['refresh'])

        self.results['access'] = str(refresh.access_token)

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            self.results['refresh'] = str(refresh)

        return True


class TokenVerifySerializer(BaseTokenSerializer):
    token = serializers.CharField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(False):
            self.err_messages['error'] = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        token = UntypedToken(self.validated_data['token'])

        if api_settings.BLACKLIST_AFTER_ROTATION:
            jti = token.get(api_settings.JTI_CLAIM)
            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                self.err_messages['detail'] = 'Token is blacklisted'
                self.err_messages['code'] = 'blacklisted_token'
                self.err_status = status.HTTP_400_BAD_REQUEST
                return False

        return True


class TokenBlacklistSerializer(BaseTokenSerializer):
    refresh = serializers.CharField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(False):
            self.err_messages = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        try:
            refresh = RefreshToken(self.validated_data['refresh'])
        except TokenError as e:
            self.err_messages['detail'] = e.args[0]
            self.err_messages['code'] = 'blacklist_token_error'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        try:
            refresh.blacklist()
        except AttributeError:
            pass

        return True
