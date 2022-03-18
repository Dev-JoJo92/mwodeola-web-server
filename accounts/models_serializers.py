from collections import OrderedDict

from django.db import IntegrityError
from django.db.models import Sum
from rest_framework import serializers, status
from rest_framework.utils.serializer_helpers import ReturnDict, BindingDict

from .models import AccountGroup, AccountDetail, Account, SNS, ICON_TYPE
from mwodeola_users.models import MwodeolaUser
from _mwodeola import exceptions
from _mwodeola.cipher import AESCipher
from rest_framework.fields import empty


class BaseSerializer(serializers.Serializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

        super().__init__(instance, data, **kwargs)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.errors
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
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.errors
            return False
        else:
            # self.results = self.data
            return True


class SnsSerializer(BaseModelSerializer):
    class Meta:
        model = SNS
        fields = '__all__'


# [AccountGroup] Serializer
class AccountGroupSerializerForCreate(BaseModelSerializer):
    mwodeola_user = serializers.PrimaryKeyRelatedField(queryset=MwodeolaUser.objects.all(), write_only=True)

    class Meta:
        model = AccountGroup
        fields = '__all__'

    def create(self, validated_data):
        sns = validated_data.get('sns', None)
        group_name = validated_data.get('group_name', None)

        if sns is None and group_name is None:
            raise exceptions.FieldExceptions(group_name='required fields')

        if sns is not None:
            validated_data['group_name'] = sns.name
            validated_data['app_package_name'] = sns.app_package_name
            validated_data['icon_type'] = 3
            validated_data.setdefault('web_url', sns.web_url)

        try:
            new_group = super().create(validated_data)
        except IntegrityError as e:
            raise exceptions.DuplicatedException(group_name=str(e))

        return new_group

    def update(self, instance, validated_data):
        return {}


# [AccountGroup] Serializer
class AccountGroupSerializerForUpdate(BaseModelSerializer):
    mwodeola_user = serializers.PrimaryKeyRelatedField(queryset=MwodeolaUser.objects.all(), write_only=True)

    class Meta:
        model = AccountGroup
        fields = '__all__'
        read_only_fields = ['sns']

    def create(self, validated_data):
        return {}

    def update(self, instance, validated_data):
        if instance.sns is not None:
            validated_data.pop('app_package_name', None)
            validated_data.pop('icon_type', None)

        try:
            group = super().update(instance, validated_data)
        except IntegrityError as e:
            raise exceptions.DuplicatedException(group_name=str(e))

        return group


# [AccountGroup] Serializer
class AccountGroupSerializerForRead(BaseModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['mwodeola_user']

    def to_representation(self, instance):
        result = super().to_representation(instance)

        detail_count = Account.objects.filter(own_group=instance.id).count()
        result['detail_count'] = detail_count

        views_sum = AccountDetail.objects.filter(group=instance.id).aggregate(Sum('views'))
        if views_sum['views__sum'] is None:
            result['total_views'] = 0
        else:
            result['total_views'] = views_sum['views__sum']
        return result


# [AccountDetail] Serializer
class AccountDetailSerializer(BaseModelSerializer):

    class Meta:
        model = AccountDetail
        exclude = ['group']

    def create(self, validated_data):
        cipher = AESCipher()
        validated_data['user_password'] = cipher.encrypt(validated_data.get('user_password', None))
        validated_data['user_password_pin4'] = cipher.encrypt(validated_data.get('user_password_pin4', None))
        validated_data['user_password_pin6'] = cipher.encrypt(validated_data.get('user_password_pin6', None))
        validated_data['user_password_pattern'] = cipher.encrypt(validated_data.get('user_password_pattern', None))

        new_detail = super().create(validated_data)
        Account.objects.create(
            own_group=new_detail.group,
            detail=new_detail
        )
        return new_detail

    def update(self, instance, validated_data):
        cipher = AESCipher()
        validated_data['user_password'] = cipher.encrypt(validated_data.get('user_password', None))
        validated_data['user_password_pin4'] = cipher.encrypt(validated_data.get('user_password_pin4', None))
        validated_data['user_password_pin6'] = cipher.encrypt(validated_data.get('user_password_pin6', None))
        validated_data['user_password_pattern'] = cipher.encrypt(validated_data.get('user_password_pattern', None))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        cipher = AESCipher()
        result = super().to_representation(instance)
        result['group'] = instance.group.id
        result['user_password'] = cipher.decrypt(instance.user_password)
        result['user_password_pin4'] = cipher.decrypt(instance.user_password_pin4)
        result['user_password_pin6'] = cipher.decrypt(instance.user_password_pin6)
        result['user_password_pattern'] = cipher.decrypt(instance.user_password_pattern)
        return result


# [AccountDetail] Serializer
class AccountDetailSerializerForRead(BaseModelSerializer):
    class Meta:
        model = AccountDetail
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['user_password'] = AESCipher().decrypt(instance.user_password)
        ret['user_password_pin4'] = AESCipher().decrypt(instance.user_password_pin4)
        ret['user_password_pin6'] = AESCipher().decrypt(instance.user_password_pin6)
        ret['user_password_pattern'] = AESCipher().decrypt(instance.user_password_pattern)
        instance.views += 1
        instance.save()
        return ret


# [AccountDetail] Serializer
class AccountDetailSerializerSimple(BaseModelSerializer):
    class Meta:
        model = AccountDetail
        fields = ['id', 'user_id']


# [Account] Serializer
class AccountSerializerForRead(BaseModelSerializer):
    account_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Account
        fields = ['account_id', 'created_at', 'own_group', 'sns_group', 'detail']

    def to_representation(self, instance):
        self.fields['own_group'] = AccountGroupSerializerForRead()
        self.fields['sns_group'] = AccountGroupSerializerForRead()
        self.fields['detail'] = AccountDetailSerializerForRead()
        return super().to_representation(instance)


# [Account] Serializer
class AccountSerializerSimpleForRead(BaseModelSerializer):
    account_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Account
        fields = ['account_id', 'created_at', 'own_group', 'sns_group', 'detail']

    def to_representation(self, instance):
        self.fields['own_group'] = AccountGroupSerializerForRead()
        self.fields['sns_group'] = AccountGroupSerializerForRead()
        self.fields['detail'] = AccountDetailSerializerSimple()
        return super().to_representation(instance)


# [Account] Serializer
class AccountSerializerSimpleForSearch(BaseModelSerializer):
    account_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Account
        fields = ['account_id', 'created_at', 'own_group', 'detail']

    def to_representation(self, instance):
        self.fields['own_group'] = AccountGroupSerializerForRead()
        self.fields['detail'] = AccountDetailSerializerSimple()
        return super().to_representation(instance)


# [AccountDetail] Serializer
# class AccountDetailSerializerSimple(BaseModelSerializer):
#     sns = serializers.SerializerMethodField()
#     group_icon_type = serializers.SerializerMethodField()
#     group_package_name = serializers.SerializerMethodField()
#     group_icon_image_url = serializers.SerializerMethodField()
#
#     class Meta:
#         model = AccountDetail
#         fields = [
#             'id',
#             'user_id',
#             'sns',
#             'group_icon_type',
#             'group_package_name',
#             'group_icon_image_url',
#         ]
#
#     def get_sns(self, obj):
#         sns = obj.group.sns
#         print(f'get_sns(): {sns}')
#         if sns is None:
#             return None
#         return sns.id
#
#     def get_group_icon_type(self, obj):
#         return obj.group.icon_type
#
#     def get_group_package_name(self, obj):
#         # return 'package'
#         return obj.group.app_package_name
#
#     def get_group_icon_image_url(self, obj):
#         # return 'url'
#         return obj.group.icon_image_url

