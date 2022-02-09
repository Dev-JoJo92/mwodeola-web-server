from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.fields import empty

from _mwodeola import exceptions
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


class AccountGroupDetail_POST_Serializer(BaseSerializer):
    own_group = serializers.DictField(write_only=True)
    detail = serializers.DictField(write_only=True)

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)

        self.group_serializer = None
        self.detail_serializer = None

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        own_group = self.validated_data['own_group']
        own_group['mwodeola_user'] = self.user.id

        detail = self.validated_data['detail']

        self.group_serializer = AccountGroupSerializerForCreate(data=own_group)
        self.detail_serializer = AccountDetailSerializer(data=detail)

        if not self.group_serializer.is_valid():
            self.err_messages = self.group_serializer.err_messages
            return False

        if not self.detail_serializer.is_valid():
            self.err_messages = self.detail_serializer.err_messages
            return False

        return True

    def save(self, **kwargs):
        new_group = self.group_serializer.save()
        self.detail_serializer.save(group=new_group)

        new_account = Account.objects.get(own_group=new_group)

        self.results = {
            'account_id': new_account.id,
            'created_at': new_account.created_at,
            'own_group': self.group_serializer.data,
            'sns_group': new_account.sns_group,
            'detail': self.detail_serializer.data
        }

        return self.results


class AccountGroupDetail_PUT_Serializer(BaseSerializer):
    own_group = serializers.DictField(write_only=True)
    detail = serializers.DictField(write_only=True)

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)

        self.group_serializer = None
        self.detail_serializer = None

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        own_group = self.validated_data['own_group']
        own_group['mwodeola_user'] = self.user.id
        detail = self.validated_data['detail']

        group_id = own_group.get('id', None)
        if group_id is None:
            raise exceptions.FieldException(id='required field')

        detail_id = detail.get('id', None)
        if detail_id is None:
            raise exceptions.FieldException(id='required field')

        try:
            group_instance = AccountGroup.objects.get(id=group_id)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise exceptions.FieldException(id=str(e))

        try:
            detail_instance = AccountDetail.objects.get(id=detail_id)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise exceptions.FieldException(id=str(e))

        if group_instance.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        if detail_instance.group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        self.group_serializer = AccountGroupSerializerForUpdate(group_instance, data=own_group)
        self.detail_serializer = AccountDetailSerializer(detail_instance, data=detail)

        if not self.group_serializer.is_valid():
            self.err_messages = self.group_serializer.err_messages
            return False

        if not self.detail_serializer.is_valid():
            self.err_messages = self.detail_serializer.err_messages
            return False

        return True

    def save(self, **kwargs):
        group = self.group_serializer.save()
        detail = self.detail_serializer.save()

        account = Account.objects.filter(own_group=group).filter(detail=detail)

        self.results = {
            'account_id': account[0].id,
            'created_at': account[0].created_at,
            'own_group': self.group_serializer.data,
            'sns_group': account[0].sns_group,
            'detail': self.detail_serializer.data
        }

        return self.results


class AccountGroupSnsDetail_POST_Serializer(BaseSerializer):
    own_group = serializers.DictField()
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(user, instance, data, **kwargs)
        self.serializer = None

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        own_group = self.validated_data['own_group']
        own_group['mwodeola_user'] = self.user.id
        own_group['sns'] = None

        sns_detail = self.validated_data['sns_detail_id']

        if sns_detail.group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        if sns_detail.group.sns is None:
            raise exceptions.FieldException(sns_detail_id='This detail is not belong to SNS group')

        self.serializer = AccountGroupSerializerForCreate(data=own_group)

        if not self.serializer.is_valid():
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.serializer.err_messages
            return False

        return True

    def save(self, **kwargs):
        new_group = self.serializer.save()
        sns_detail = self.validated_data['sns_detail_id']

        new_account = Account.objects.create(
            own_group=new_group,
            sns_group=sns_detail.group,
            detail=sns_detail
        )

        sns_group_dict = AccountGroupSerializerForRead(sns_detail.group).data
        sns_detail_dict = AccountDetailSerializerForRead(sns_detail).data

        self.results = {
            'account_id': new_account.id,
            'created_at': new_account.created_at,
            'own_group': self.serializer.data,
            'sns_group': sns_group_dict,
            'detail': sns_detail_dict
        }

        return self.results


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

        own_group_dict = AccountGroupSerializerForRead(own_group).data
        sns_group_dict = AccountGroupSerializerForRead(sns_detail.group).data
        sns_detail_dict = AccountDetailSerializerForRead(sns_detail).data

        self.results = {
            'account_id': new_account.id,
            'created_at': new_account.created_at,
            'own_group': own_group_dict,
            'sns_group': sns_group_dict,
            'detail': sns_detail_dict
        }

        return self.results


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
    group = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all(), write_only=True)

    class Meta:
        model = AccountDetail
        fields = '__all__'

    def __init__(self, user=None, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user

    def is_valid(self, raise_exception=False):
        if self.user is None:
            self.err_messages['message'] = 'User not found'
            self.err_messages['code'] = 'user_not_found'
            self.err_status = status.HTTP_401_UNAUTHORIZED
            return None
        if not super().is_valid(raise_exception):
            return False

        group = self.validated_data['group']

        if group.mwodeola_user.id != self.user.id:
            raise exceptions.NotOwnerDataException()

        return True

    def create(self, validated_data):
        new_detail = super().create(validated_data)

        new_account = Account.objects.get(detail=new_detail)

        own_group_dict = AccountGroupSerializerForRead(new_account.own_group).data
        detail_dict = AccountDetailSerializerForRead(new_detail).data

        self.results = {
            'account_id': new_account.id,
            'created_at': new_account.created_at,
            'own_group': own_group_dict,
            'sns_group': None,
            'detail': detail_dict
        }

        return self.results


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

