from django.db import IntegrityError
from rest_framework import serializers, status, exceptions
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import AccountGroup, AccountDetail, Account, SNS, ICON_TYPE
from mwodeola_users.models import MwodeolaUser
from _mwodeola.cipher import AESCipher
from rest_framework.fields import empty


CIPHER = AESCipher()


class BaseSerializer(serializers.Serializer):

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        self.user = user
        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

        super().__init__(instance, data, **kwargs)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages = self.errors
            return False
        if self.user is None:
            self.err_messages['error'] = 'Server Error (500)'
            self.err_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return False
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
            return False
        else:
            # self.results = self.data
            return True


class SnsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNS
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForCreate(BaseSerializer):
    mwodeola_user = serializers.PrimaryKeyRelatedField(queryset=MwodeolaUser.objects.all(), write_only=True)
    id = serializers.UUIDField(read_only=True)
    sns = serializers.PrimaryKeyRelatedField(queryset=SNS.objects.all(), allow_null=True, default=None)
    group_name = serializers.CharField(max_length=30, default=None)
    app_package_name = serializers.CharField(max_length=100, default=None)
    web_url = serializers.CharField(max_length=100, default=None)
    icon_type = serializers.ChoiceField(choices=ICON_TYPE, default=0)
    icon_image_url = serializers.URLField(max_length=500, allow_null=True, default=None)
    is_favorite = serializers.BooleanField(default=False)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False
        sns = self.validated_data['sns']
        group_name = self.validated_data['group_name']

        if sns is None and group_name is None:
            self.err_messages['group_name'] = 'This is required field'
            return False
        return True

    def create(self, validated_data):
        kwargs = dict()

        for key in validated_data:
            kwargs[key] = validated_data.get(key, None)

        sns = validated_data['sns']

        if sns is not None:
            kwargs['group_name'] = sns.name
            kwargs['app_package_name'] = sns.app_package_name
            kwargs['web_url'] = sns.web_url
            kwargs['icon_type'] = 3
            kwargs.pop('icon_image_url')

        try:
            new_group = AccountGroup.objects.create(**kwargs)
        except (IntegrityError, ValueError) as e:
            raise exceptions.ValidationError(e.args[0])

        return new_group

    def update(self, instance, validated_data):
        pass


# [AccountGroup] Serializer
class AccountGroupSerializerForRead(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['mwodeola_user']


# [AccountGroup] Serializer
class AccountGroupSerializerForUpdate(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['sns', 'icon_image_url']


# [AccountDetail] Serializer
class AccountDetailSerializer(BaseModelSerializer):
    class Meta:
        model = AccountDetail
        exclude = ['group']

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

    @property
    def data(self):
        data = super().data
        data['user_password'] = AESCipher().decrypt(data['user_password'])
        data['user_password_pin'] = AESCipher().decrypt(data['user_password_pin'])
        data['user_password_pattern'] = AESCipher().decrypt(data['user_password_pattern'])
        return ReturnDict(data, serializer=self)


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



