from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, status
from rest_framework.fields import empty

from _mwodeola.cipher import AESCipher
from mwodeola_users.models import MwodeolaUser
from .models import SNS, AccountGroup, AccountDetail, Account
from .serializers_base import (
    AccountGroupSerializerForRead,
    AccountGroupSerializerForCreate,
    AccountGroupSerializerForUpdate,
    AccountDetailSerializer,
    AccountDetailSerializerSimple,
    AccountSerializerForRead,
)

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


class BaseNestedSerializer:
    account_group_serializer = None
    account_detail_serializer = None

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        if data.get('account_group', None) is None:
            raise exceptions.ParseError('account_group is required')
        if data.get('detail', None) is None:
            raise exceptions.ParseError('detail is required')

        data['account_group']['mwodeola_user'] = user.id

        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self) -> bool:
        valid = True
        if not self.account_group_serializer.is_valid():
            self.err_messages['account_group_errors'] = self.account_group_serializer.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            valid = False
        if not self.account_detail_serializer.is_valid():
            self.err_messages['account_detail_errors'] = self.account_detail_serializer.errors
            self.err_status = status.HTTP_400_BAD_REQUEST
            valid = False
        return valid

    def save(self):
        self.account_group_serializer.save()
        self.account_detail_serializer.save()
        self.results['account_group'] = self.account_group_serializer.data
        self.results['detail'] = self.account_detail_serializer.data


class AccountGroup_GET_Serializer(AccountGroupSerializerForRead):
    pass


class AccountGroup_PUT_Serializer(AccountGroupSerializerForUpdate):
    pass


class AccountGroup_DELETE_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']

        if account_group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        return True

    def delete(self):
        self.validated_data['account_group_id'].delete()


class AccountGroupFavorite_PUT_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    is_favorite = serializers.BooleanField()

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']

        if account_group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        return True

    def create(self, validated_data):
        group = validated_data['account_group_id']
        is_favorite = validated_data['is_favorite']
        group.is_favorite = is_favorite
        group.save()
        return group


class AccountGroupDetail_GET_Serializer(BaseSerializer):
    account_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_detail = self.validated_data['account_detail_id']

        if account_detail.group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        account_detail.views += 1
        account_detail.save()

        group_serializer = AccountGroupSerializerForRead(account_detail.group)
        detail_serializer = AccountDetailSerializer(account_detail)

        self.results['account_group'] = group_serializer.data
        self.results['detail'] = detail_serializer.data
        return True


class AccountGroupDetail_POST_Serializer(BaseNestedSerializer):
    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)
        account_group_data = data['account_group']
        account_detail_data = data['detail']

        self.account_group_serializer = AccountGroupSerializerForCreate(user=user, data=account_group_data)
        self.account_detail_serializer = AccountDetailSerializer(data=account_detail_data)

    def save(self):
        try:
            new_group = self.account_group_serializer.save()
        except IntegrityError as e:
            raise exceptions.ValidationError(e.args[0])

        self.account_detail_serializer.save(group=new_group)
        self.results['account_group'] = self.account_group_serializer.data
        self.results['detail'] = self.account_detail_serializer.data


class AccountGroupDetail_PUT_Serializer(BaseNestedSerializer):
    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)
        account_group_data = data['account_group']
        account_detail_data = data['detail']

        try:
            account_group_id = account_group_data['id']
            qs_account_group = AccountGroup.objects.get(id=account_group_id)
        except KeyError:
            raise exceptions.ParseError("account_group's id is required fields.")

        try:
            account_detail_id = account_detail_data['id']
            qs_account_detail = AccountDetail.objects.get(id=account_detail_id)
        except KeyError:
            raise exceptions.ParseError("detail's id is required fields.")

        self.account_group_serializer = AccountGroupSerializerForUpdate(
            qs_account_group, data=account_group_data)
        self.account_detail_serializer = AccountDetailSerializer(
            qs_account_detail, data=account_detail_data)


class AccountGroupSnsDetail_POST_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']
        sns_detail = self.validated_data['sns_detail_id']

        if account_group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        if account_group.sns is not None:
            self.err_messages['error'] = 'account_group must be no sns'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        if sns_detail.group.sns is None:
            self.err_messages['error'] = 'sns_detail must be sns'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        return True

    def create(self, validated_data):
        own_group = validated_data['account_group_id']
        sns_detail = validated_data['sns_detail_id']

        try:
            new_account = Account.objects.create(
                own_group=own_group,
                sns_group=sns_detail.group,
                detail=sns_detail
            )
        except IntegrityError as e:
            raise exceptions.ValidationError(e.args[0])

        return new_account


class AccountGroupSnsDetail_DELETE_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']
        sns_detail = self.validated_data['sns_detail_id']

        if account_group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        if account_group.sns is not None:
            self.err_messages['error'] = 'account_group must be no sns'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        if sns_detail.group.sns is None:
            self.err_messages['error'] = 'sns_detail must be sns'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        accounts = Account.objects.filter(own_group=account_group)

        try:
            target_account = accounts.get(detail=sns_detail)
        except ObjectDoesNotExist as e:
            self.err_messages['error'] = e.args[0]
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        if len(accounts) == 1:
            self.instance = account_group
        else:
            self.instance = target_account

        return True

    def delete(self):
        self.instance.delete()


class AccountGroupDetailAllSerializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']

        if account_group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        accounts = Account.objects.filter(own_group=account_group)

        details = []
        for account in accounts:
            details.append(account.detail)

        serializer = AccountDetailSerializerSimple(details, many=True)

        self.results['group_id'] = account_group.id
        self.results['group_name'] = account_group.group_name
        self.results['details'] = serializer.data
        return True


class AccountDetail_POST_Serializer(AccountDetailSerializer):
    class Meta:
        model = AccountDetail
        fields = '__all__'


class AccountDetail_DELETE_Serializer(BaseSerializer):
    account_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_detail = self.validated_data['account_detail_id']

        if account_detail.group.mwodeola_user.id != self.user.id:
            self.err_messages['error'] = 'Forbidden (403)'
            self.err_status = status.HTTP_403_FORBIDDEN
            return False

        return True

    def delete(self):
        account_detail = self.validated_data['account_detail_id']

        accounts = Account.objects.filter(own_group=account_detail.group)

        if len(accounts) == 1:
            account_detail.group.delete()
        else:
            account_detail.delete()


class AccountSearchGroupSerializer(AccountGroupSerializerForRead):
    pass


class AccountSearchDetailSerializer(AccountDetailSerializerSimple):
    pass

