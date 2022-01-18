from rest_framework import serializers
from .models import AccountGroup, AccountDetail, Account, SNS
from mwodeola_users.models import MwodeolaUser
from _mwodeola.cipher import AESCipher
from rest_framework.fields import empty


CIPHER = AESCipher()


class SnsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNS
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForRead(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['mwodeola_user']


# [AccountGroup] Serializer
class AccountGroupSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['sns']


# [AccountDetail] Serializer
class AccountDetailSerializerForRead(serializers.ModelSerializer):
    class Meta:
        model = AccountDetail
        fields = '__all__'

    def to_representation(self, instance):
        instance.user_password = CIPHER.decrypt(instance.user_password)
        instance.user_password_pin = CIPHER.decrypt(instance.user_password_pin)
        instance.user_password_pattern = CIPHER.decrypt(instance.user_password_pattern)
        return super().to_representation(instance)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


# [AccountDetail] Serializer
class AccountDetailSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = AccountDetail
        fields = '__all__'
        read_only_fields = ['group']

    def create(self, validated_data):
        validated_data['user_password'] = \
            AESCipher().encrypt(validated_data['user_password'])
        try:
            validated_data['user_password_pin'] = \
                AESCipher().encrypt(validated_data['user_password_pin'])
        except KeyError:
            pass
        try:
            validated_data['user_password_pattern'] = \
                AESCipher().encrypt(validated_data['user_password_pattern'])
        except KeyError:
            pass

        new_detail = super().create(validated_data)
        Account.objects.create(
            own_group=new_detail.group,
            detail=new_detail
        )
        return new_detail


# [AccountDetail] Serializer
class AccountDetailSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = AccountDetail
        exclude = ['group']

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        validated_data['user_password'] = \
            CIPHER.encrypt(validated_data['user_password'])
        try:
            validated_data['user_password_pin'] = \
                CIPHER.encrypt(validated_data['user_password_pin'])
        except KeyError:
            pass
        try:
            validated_data['user_password_pattern'] = \
                CIPHER.encrypt(validated_data['user_password_pattern'])
        except KeyError:
            pass
        return super().update(instance, validated_data)


# [Account] Serializer
class AccountSerializerForRead(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'



