from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.fields import empty

from _mwodeola import exceptions
from _mwodeola.cipher import AESCipher
from mwodeola_users.models import MwodeolaUser
from .models import SNS, AccountGroup, AccountDetail, Account
from .models_serializers import (
    AccountGroupSerializerForRead,
    AccountGroupSerializerForCreate,
    AccountGroupSerializerForUpdate,
    AccountDetailSerializer,
    AccountDetailSerializerForRead,
    AccountDetailSerializerSimple,
    AccountSerializerForRead,
    AccountSerializerSimpleForRead,
    AccountSerializerSimpleForSearch,
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
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.errors
            return False
        if self.user is None:
            self.err_messages['message'] = 'Server Error (500)'
            self.err_messages['code'] = 'server_error'
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
            raise exceptions.FieldException(account_group='required field')
        if data.get('detail', None) is None:
            raise exceptions.FieldException(detail='required field')

        data['account_group']['mwodeola_user'] = user.id

        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self) -> bool:
        valid = True
        if not self.account_group_serializer.is_valid():
            self.err_messages['account_group'] = self.account_group_serializer.err_messages
            self.err_status = status.HTTP_400_BAD_REQUEST
            valid = False
        if not self.account_detail_serializer.is_valid():
            self.err_messages['detail'] = self.account_detail_serializer.err_messages
            self.err_status = status.HTTP_400_BAD_REQUEST
            valid = False
        return valid

    def save(self):
        try:
            self.account_group_serializer.save()
        except IntegrityError as e:
            raise exceptions.DuplicatedException(group_name=str(e))
        self.account_detail_serializer.save()
        self.results['account_group'] = self.account_group_serializer.data
        self.results['detail'] = self.account_detail_serializer.data


class AccountGroup_GET_Serializer(AccountGroupSerializerForRead):
    pass


class AccountGroup_PUT_Serializer(AccountGroupSerializerForUpdate):

    def save(self, **kwargs):
        try:
            ret = super().save(**kwargs)
        except IntegrityError as e:
            raise exceptions.DuplicatedException(group_name=str(e))
        return ret


class AccountGroup_DELETE_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']

        if account_group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

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
            raise exceptions.NotOwnerDataException()

        return True

    def create(self, validated_data):
        group = validated_data['account_group_id']
        is_favorite = validated_data['is_favorite']
        group.is_favorite = is_favorite
        group.save()
        return group


class AccountGroupDetail_GET_Serializer(BaseSerializer):
    account_id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account = self.validated_data['account_id']

        if account.own_group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        # SNS 그룹에 연결된 detail 의 요청은 views 를 올리지 않음.
        if account.sns_group is None:
            account.detail.views += 1
            account.detail.save()

        serializer = AccountSerializerForRead(account)

        self.results = serializer.data

        return True


class AccountGroupDetail_POST_Serializer(BaseNestedSerializer):
    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)
        account_group_data = data['account_group']
        account_detail_data = data['detail']

        self.account_group_serializer = AccountGroupSerializerForCreate(data=account_group_data)
        self.account_detail_serializer = AccountDetailSerializer(data=account_detail_data)

    def save(self):
        try:
            new_group = self.account_group_serializer.save()
        except IntegrityError as e:
            raise exceptions.DuplicatedException(group_name=str(e))

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
            account_group = AccountGroup.objects.get(id=account_group_id)
        except KeyError:
            raise exceptions.FieldException(id='required field')
        except ValidationError as e:
            raise exceptions.FieldException(id=str(e))

        if account_group.mwodeola_user.id != user.id:
            raise exceptions.NotOwnerDataException()

        try:
            account_detail_id = account_detail_data['id']
            account_detail = AccountDetail.objects.get(id=account_detail_id)
        except KeyError:
            raise exceptions.FieldException(id='required field')
        except ValidationError as e:
            raise exceptions.FieldException(id=str(e))

        if account_detail.group.mwodeola_user.id != user.id:
            raise exceptions.NotOwnerDataException()

        self.account_group_serializer = AccountGroupSerializerForUpdate(
            account_group, data=account_group_data)
        self.account_detail_serializer = AccountDetailSerializer(
            account_detail, data=account_detail_data)


class AccountGroupSnsDetail_POST_Serializer(BaseSerializer):
    account_group = serializers.DictField()
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)
        self.serializer = None

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group_dict = self.validated_data['account_group']
        account_group_dict['mwodeola_user'] = self.user.id

        self.serializer = AccountGroupSerializerForCreate(data=account_group_dict)

        if not self.serializer.is_valid():
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.serializer.err_messages
            return False

        return True

    def save(self, **kwargs):
        new_group = self.serializer.save()
        sns_detail = self.validated_data['sns_detail_id']

        Account.objects.create(
            own_group=new_group,
            sns_group=sns_detail.group,
            detail=sns_detail
        )

        return {
            'account_group': self.serializer.data,
            'detail': AccountDetailSerializerForRead(sns_detail).data
        }


class AccountGroupSnsDetail_PUT_Serializer(BaseSerializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account_group = self.validated_data['account_group_id']
        sns_detail = self.validated_data['sns_detail_id']

        if account_group.mwodeola_user.id != self.user.id or sns_detail.group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        if account_group.sns is not None:
            self.err_messages['message'] = 'account_group must be no sns'
            self.err_messages['code'] = 'sns_error_1'
            self.err_status = status.HTTP_400_BAD_REQUEST
            return False

        if sns_detail.group.sns is None:
            self.err_messages['message'] = 'sns_detail must be sns'
            self.err_messages['code'] = 'sns_error_2'
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
            raise exceptions.DuplicatedException(sns_detail_id=str(e))

        return new_account


class AccountGroupSnsDetail_DELETE_Serializer(BaseSerializer):
    account_id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        account = self.validated_data['account_id']

        if account.own_group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        if Account.objects.filter(own_group=account.own_group).count() == 1:
            self.instance = account.own_group
        else:
            self.instance = account

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
            raise exceptions.NotOwnerDataException()

        accounts = Account.objects.filter(own_group=account_group)

        group_serializer = AccountGroupSerializerForRead(account_group)
        account_serializer = AccountSerializerSimpleForRead(accounts, many=True)

        self.results['own_group'] = group_serializer.data
        self.results['accounts'] = account_serializer.data

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
            raise exceptions.NotOwnerDataException()

        return True

    def delete(self):
        account_detail = self.validated_data['account_detail_id']

        accounts = Account.objects.filter(own_group=account_detail.group)

        if len(accounts) == 1:
            account_detail.group.delete()
        else:
            account_detail.delete()


class AccountSearchGroupSerializer(BaseSerializer):
    group_name = serializers.CharField(max_length=30)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        group_name = self.validated_data['group_name']

        groups = AccountGroup.objects\
            .filter(mwodeola_user=self.user)\
            .filter(group_name__contains=group_name)

        serializer = AccountGroupSerializerForRead(groups, many=True)

        self.results = serializer.data
        return True


class AccountSearchDetailSerializer(BaseSerializer):
    user_id = serializers.CharField(max_length=100)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        user_id = self.validated_data['user_id']

        details = AccountDetail.objects.filter(user_id__contains=user_id)
        detail_ids = []
        for detail in details:
            if detail.group.mwodeola_user.id == self.user.id:
                detail_ids.append(detail.id)

        accounts = Account.objects.filter(detail__in=detail_ids)

        serializer = AccountSerializerSimpleForSearch(accounts, many=True)

        self.results = serializer.data
        return True

