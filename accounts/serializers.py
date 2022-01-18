from abc import abstractmethod

from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework.fields import empty

from mwodeola_users.models import MwodeolaUser
from .models import SNS, AccountGroup, AccountDetail, Account
from .serializers_base import (
    SnsSerializer,
    AccountGroupSerializerForRead,
    AccountGroupSerializerForCreate,
    AccountGroupSerializerForUpdate,
    AccountDetailSerializerForRead,
    AccountDetailSerializerForCreate,
    AccountDetailSerializerForUpdate,
    AccountSerializerForRead,
)


class NestedSerializer:
    data = {}
    errors = {}

    account_group_serializer = None
    account_detail_serializer = None

    def __init__(self, instance=None, data=empty, **kwargs):
        data['account_group']['mwodeola_user'] = kwargs.pop('user_id')

    def is_valid(self) -> bool:
        valid = True
        if not self.account_group_serializer.is_valid():
            self.errors['account_group_errors'] = self.account_group_serializer.errors
            valid = False
        if not self.account_detail_serializer.is_valid():
            self.errors['account_detail_errors'] = self.account_detail_serializer.errors
            valid = False
        return valid

    def save(self):
        self.account_group_serializer.save()
        self.account_detail_serializer.save()
        self.data['account_group'] = self.account_group_serializer.data
        self.data['detail'] = self.account_detail_serializer.data


class GET_AccountGroupSerializer(AccountGroupSerializerForRead):
    pass


class POST_AccountGroupSerializer(NestedSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        account_group_data = data['account_group']
        account_detail_data = data['detail']

        self.account_group_serializer = AccountGroupSerializerForCreate(data=account_group_data)
        self.account_detail_serializer = AccountDetailSerializerForCreate(data=account_detail_data)

    def save(self):
        try:
            new_group = self.account_group_serializer.save()
        except IntegrityError as e:
            raise exceptions.ValidationError(e)

        self.account_detail_serializer.save(group=new_group)
        self.data['account_group'] = self.account_group_serializer.data
        self.data['detail'] = self.account_detail_serializer.data


class PUT_AccountGroupSerializer(NestedSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
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
        self.account_detail_serializer = AccountDetailSerializerForUpdate(
            qs_account_detail, data=account_detail_data)


class AccountGroupAddSnsDetailSerializer(serializers.Serializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())

    def is_valid(self, raise_exception=False):
        if super().is_valid(raise_exception):
            group = self.validated_data['account_group_id']
            sns_detail = self.validated_data['sns_detail_id']

            if group.sns is not None:
                raise exceptions.ParseError("account_group_id must not be SNS Group")
            if sns_detail.group.sns is None:
                raise exceptions.ParseError("sns_detail_id's group must be SNS Group")

            return True
        else:
            return False

    def create(self, validated_data):
        print('create()')
        own_group = validated_data['account_group_id']
        sns_detail = validated_data['sns_detail_id']

        try:
            Account.objects.create(
                own_group=own_group,
                sns_group=sns_detail.group,
                detail=sns_detail
            )
        except IntegrityError as e:
            raise exceptions.ValidationError(e)

        return validated_data

    def update(self, instance, validated_data):
        pass


class AccountGroupFavoriteSerializer(serializers.Serializer):
    account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
    is_favorite = serializers.BooleanField()

    def create(self, validated_data):
        group = validated_data['account_group_id']
        is_favorite = validated_data['is_favorite']
        group.is_favorite = is_favorite
        group.save()
        return validated_data

    def update(self, instance, validated_data):
        pass


class GET_AccountDetailSerializer(AccountDetailSerializerForRead):
    sns_group = serializers.SerializerMethodField()

    def get_sns_group(self, obj):
        sns = obj.group.sns
        if sns is None:
            return None
        else:
            return sns.name


class POST_AccountDetailSerializer(AccountDetailSerializerForCreate):
    class Meta:
        model = AccountDetail
        fields = '__all__'


class SearchAccountGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        exclude = ['mwodeola_user']
