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
            self.err_messages = self.errors
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
            self.err_messages = self.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False
        return True


class SignUpVerifySerializer(BaseSerializer):
    phone_number = serializers.CharField(max_length=16)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        phone_number = self.validated_data['phone_number']

        query_set = MwodeolaUser.objects.filter(phone_number=phone_number)
        if query_set.exists():
            self.err_messages['error'] = 'already joined'
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


class AutoSignInSerializer(BaseSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        self.user = kwargs.pop('user', None)
        self.old_refresh = kwargs.pop('refresh_token', None)
        super().__init__(instance, data, **kwargs)

    def is_valid(self, raise_exception=False):
        if self.user is None or self.old_refresh is None:
            self.err_messages['error'] = 'Server Error (500)'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False

        try:
            RefreshToken(self.old_refresh).blacklist()
        except TokenError as e:
            self.err_messages['error'] = e.args[0]
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
            self.err_messages['error'] = 'Server Error (500)'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False
        if not super().is_valid(raise_exception):
            return False

        phone_number = self.validated_data['phone_number']
        password = self.validated_data['password']

        user = self.get_user_by_authentication_rule(phone_number, password)

        return user is not None

    def delete(self):
        self.instance.delete()


class PasswordAuthSerializer(UserAuthMixin, BaseSerializer):
    password = PasswordField()

    def is_valid(self, raise_exception=False):
        if self.instance is None:
            self.err_messages['error'] = 'Server Error (500)'
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
            self.err_messages['error'] = 'Server Error (500)'
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



