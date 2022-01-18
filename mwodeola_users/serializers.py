from abc import ABC

from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from .models import MwodeolaUser


class MwodeolaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MwodeolaUser
        fields = '__all__'

    def create(self, validated_data):
        return MwodeolaUser.objects.create_user(**validated_data)
        # return User.objects.create_superuser(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class SignUpSerializer(serializers.Serializer):
    TAG = 'SignUpSerializer'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['user_name'] = serializers.CharField(max_length=20)
        self.fields['email'] = serializers.EmailField(max_length=50)
        self.fields['phone_number'] = serializers.CharField(max_length=16)
        self.fields['password'] = serializers.CharField(max_length=30)

    def validate(self, attrs):
        # print(f'{self.TAG}.validate(): attrs={attrs}')
        data = {}

        user_name = attrs['user_name']
        email = attrs['email']
        phone_number = attrs['phone_number']
        password = attrs['password']

        user = MwodeolaUser.objects.create_user(
            user_name, email, phone_number, password)

        refresh = RefreshToken.for_user(user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return data


