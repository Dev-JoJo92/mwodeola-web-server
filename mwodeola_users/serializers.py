from abc import ABC
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status, exceptions
from rest_framework.fields import empty
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from .models import MwodeolaUser
from .auth.mixins import UserAuthMixin
from .serializers_token import (
    TokenObtainPairSerializer,
    TokenBlacklistSerializer,
    PasswordField,
)


class BaseSerializer(serializers.Serializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages['detail'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['errors'] = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        else:
            return True

    def create(self, validated_data):
        return {}

    def update(self, instance, validated_data):
        return {}


class BaseModelSerializer(serializers.ModelSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages['detail'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['errors'] = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        return True


class SignUpVerifyPhoneSerializer(BaseSerializer):
    phone_number = serializers.CharField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        phone_number = self.validated_data['phone_number']

        query_set = MwodeolaUser.objects.filter(phone_number=phone_number)
        if query_set.exists():
            self.err_messages['detail'] = 'Already registered phone number'
            self.err_messages['code'] = 'already_registered_phone_number'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        else:
            return True


class SignUpVerifyEmailSerializer(BaseSerializer):
    email = serializers.EmailField(max_length=255)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        email = self.validated_data['email']

        query_set = MwodeolaUser.objects.filter(email=email)
        if query_set.exists():
            self.err_messages['detail'] = 'Already registered email'
            self.err_messages['code'] = 'already_registered_email'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        else:
            return True


class SignUpSerializer(BaseModelSerializer):
    class Meta:
        model = MwodeolaUser
        fields = '__all__'

    def create(self, validated_data):
        user_name = validated_data['user_name']
        email = validated_data['email']
        phone_number = validated_data['phone_number']
        password = validated_data['password']

        user = MwodeolaUser.objects.create_user(
            user_name, email, phone_number, password)

        refresh = RefreshToken.for_user(user)

        self.results['refresh'] = str(refresh)
        self.results['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return user


class SignInSerializer(TokenObtainPairSerializer):
    pass


class SignInVerifySerializer(BaseSerializer):
    phone_number = serializers.CharField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        phone_number = self.validated_data['phone_number']

        query_set = MwodeolaUser.objects.filter(phone_number=phone_number)
        if query_set.exists():
            return True
        else:
            self.err_messages['detail'] = 'Unregistered users'
            self.err_messages['code'] = 'unregistered_users'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False


class SignInAutoSerializer(BaseSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        self.user = kwargs.pop('user', None)
        self.old_refresh = kwargs.pop('refresh_token', None)
        super().__init__(instance, data, **kwargs)

    def is_valid(self, raise_exception=False):
        if self.user is None or self.old_refresh is None:
            self.err_messages['detail'] = 'Server Error (500)'
            self.err_messages['code'] = 'server_error'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False

        try:
            RefreshToken(self.old_refresh).blacklist()
        except TokenError as e:
            self.err_messages['detail'] = e.args[0]
            self.err_messages['code'] = 'blacklist_token_error'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        refresh = RefreshToken.for_user(self.user)

        self.results['refresh'] = str(refresh)
        self.results['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return True


class SignOutSerializer(TokenBlacklistSerializer):
    pass


class WithdrawalSerializer(UserAuthMixin, BaseSerializer):
    phone_number = serializers.CharField()
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if self.instance is None:
            self.err_messages['detail'] = 'Server Error (500)'
            self.err_messages['code'] = 'server_error'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False
        if not super().is_valid(raise_exception):
            return False

        phone_number = self.validated_data['phone_number']
        password = self.validated_data['password']

        authed_user = self.get_user_by_authentication_rule(phone_number, password)
        token_user = self.instance

        if authed_user is None:
            return False
        if authed_user.id != token_user.id:
            self.err_messages['detail'] = 'Are you hacker?'
            self.err_messages['code'] = 'hacker_suspicion'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        return True

    def delete(self):
        self.instance.delete()


class PasswordAuthSerializer(UserAuthMixin, BaseSerializer):
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if self.instance is None:
            self.err_messages['detail'] = 'Server Error (500)'
            self.err_messages['code'] = 'server_error'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False
        if not super().is_valid(False):
            return False

        user = self.get_user_by_authentication_rule(
            phone_number=self.instance.phone_number,
            password=self.validated_data.get('password', None)
        )

        return user is not None


class PasswordChangeSerializer(BaseSerializer, UserAuthMixin):
    old_password = PasswordField()
    new_password = PasswordField()

    def is_valid(self, raise_exception=False):
        if self.instance is None:
            self.err_messages['detail'] = 'Server Error (500)'
            self.err_messages['code'] = 'server_error'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False
        if not super().is_valid(raise_exception):
            return False

        user = self.get_user_by_authentication_rule(
            phone_number=self.instance.phone_number,
            password=self.validated_data['old_password']
        )

        # 매우 매우 중요!!
        self.instance = user
        return user is not None

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        new_password = validated_data['new_password']
        instance.set_password(new_password)
        instance.save()
        return {}


class UserWakeUpSerializer(BaseSerializer, UserAuthMixin):
    phone_number = serializers.CharField()
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        user = self.get_user_for_inactive_user(
            self.validated_data['phone_number'],
            self.validated_data['password']
        )

        self.instance = user
        return user is not None

    def update(self, instance, validated_data):
        instance.is_active = True
        instance.save()
        return {}


class UserUnlockSerializer(BaseSerializer, UserAuthMixin):
    phone_number = serializers.CharField()
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        user = self.get_user_for_inactive_user(
            self.validated_data['phone_number'],
            self.validated_data['password']
        )

        self.instance = user
        return user is not None

    def update(self, instance, validated_data):
        instance.is_locked = False
        instance.is_active = True
        instance.save()
        return {}

