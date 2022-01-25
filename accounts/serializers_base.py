from rest_framework import serializers, status
from .models import AccountGroup, AccountDetail, Account, SNS
from mwodeola_users.models import MwodeolaUser
from _mwodeola.cipher import AESCipher
from rest_framework.fields import empty


CIPHER = AESCipher()


class BaseModelSerializer(serializers.ModelSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages = self.errors
            return False
        else:
            # self.results = self.data
            return True


class SnsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNS
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForRead(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['mwodeola_user']


# [AccountGroup] Serializer
class AccountGroupSerializerForCreate(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForUpdate(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['sns', 'icon_image_url']


# [AccountDetail] Serializer
class AccountDetailSerializerForRead(BaseModelSerializer):
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
class AccountDetailSerializerForCreate(BaseModelSerializer):
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
class AccountDetailSerializerForUpdate(BaseModelSerializer):
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


# [AccountDetail] Serializer
class AccountDetailSerializerSimple(BaseModelSerializer):
    is_sns_group = serializers.SerializerMethodField()
    group_icon_type = serializers.SerializerMethodField()
    group_package_name = serializers.SerializerMethodField()
    group_icon_image_url = serializers.SerializerMethodField()

    class Meta:
        model = AccountDetail
        fields = [
            'id',
            'user_id',
            'is_sns_group',
            'group_icon_type',
            'group_package_name',
            'group_icon_image_url',
        ]

    def get_is_sns_group(self, obj):
        return obj.group.sns is not None

    def get_group_icon_type(self, obj):
        return obj.group.icon_type

    def get_group_package_name(self, obj):
        # return 'package'
        return obj.group.app_package_name

    def get_group_icon_image_url(self, obj):
        # return 'url'
        return obj.group.icon_image_url


# [Account] Serializer
class AccountSerializerForRead(BaseModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'



