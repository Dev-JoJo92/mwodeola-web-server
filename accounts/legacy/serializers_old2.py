# import uuid
# from abc import ABCMeta, abstractmethod
# from collections import Counter, OrderedDict
# from django.core.exceptions import ObjectDoesNotExist, ValidationError
# from django.utils.translation import gettext_lazy as _
# from rest_framework import exceptions, serializers
# from rest_framework.fields import empty
#
# from mwodeola_users.models import MwodeolaUser
# from .models import SNS, AccountGroup, AccountDetail, Account
# from .serializers_base import (
#     SnsSerializer,
#     AccountGroupSerializerForCreate,
#     AccountGroupSerializerForUpdate,
#     AccountDetailSerializerForCreate,
#     AccountDetailSerializerForUpdate,
#     AccountSerializer,
#     BaseSerializer,
# )
#
#
# class BaseModelSerializer(serializers.ModelSerializer):
#     def __init__(self, instance=None, data=empty, **kwargs):
#         self.user_id = kwargs.pop('user_id')
#         super().__init__(instance, data, **kwargs)
#
#
# class AccountGroupCreateWithNewDetailSerializer(serializers.Serializer):
#     account_group = AccountGroupSerializerForCreate()
#     details = AccountDetailSerializerForCreate(many=True)
#
#     def __init__(self, instance=None, data=empty, **kwargs):
#         data['account_group']['mwodeola_user'] = kwargs.pop('user_id')
#         super().__init__(instance, data, **kwargs)
#
#     def create(self, validated_data):
#         account_group_data = validated_data.pop('account_group')
#         new_group = AccountGroup.objects.create(
#             **account_group_data
#         )
#
#         details = validated_data.pop('details')
#         for detail in details:
#             new_detail = AccountDetail.objects.create(
#                 group=new_group,
#                 **detail
#             )
#             Account.objects.create(
#                 own_group=new_group,
#                 sns_group=None,
#                 detail=new_detail
#             )
#         return new_group
#
#     def update(self, instance, validated_data):
#         pass
#
#
# class AccountGroupCreateWithSnsDetailSerializer(serializers.Serializer):
#     account_group = AccountGroupSerializerForCreate()
#     sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())
#
#     default_error_messages = {
#         'detail_is_not_sns': _('sns_detail_id does not belong to an SNS group.')
#     }
#
#     def __init__(self, instance=None, data=empty, **kwargs):
#         data['account_group']['mwodeola_user'] = kwargs.pop('user_id')
#         data['sns'] = None
#         super().__init__(instance, data, **kwargs)
#
#     def validate(self, attrs):
#         if attrs['sns_detail_id'].group.sns is None:
#             raise exceptions.ParseError(self.error_messages['detail_is_not_sns'])
#         return super().validate(attrs)
#
#     def create(self, validated_data):
#         account_group_data = validated_data.pop('account_group')
#         new_group = AccountGroup.objects.create(
#             **account_group_data
#         )
#
#         sns_detail = validated_data.pop('sns_detail_id')
#         Account.objects.create(
#             own_group=new_group,
#             sns_group=sns_detail.group,
#             detail=sns_detail
#         )
#         return new_group
#
#     def update(self, instance, validated_data):
#         pass
#
#
# class AccountGroupAddSnsDetailSerializer(serializers.Serializer):
#     account_group_id = serializers.PrimaryKeyRelatedField(queryset=AccountGroup.objects.all())
#     sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())
#
#     default_error_messages = {
#         'is_sns_group': _('account_group_id must not be an SNS group.'),
#         'is_not_sns_detail': _('sns_detail_id does not belong to an SNS group.')
#     }
#
#     def validate(self, attrs):
#         if attrs['account_group_id'].sns is not None:
#             raise exceptions.ParseError(self.error_messages['is_sns_group'])
#         if attrs['sns_detail_id'].group.sns is None:
#             raise exceptions.ParseError(self.error_messages['is_not_sns_detail'])
#         return attrs
#
#     def create(self, validated_data):
#         own_group = validated_data.pop('account_group_id')
#         sns_detail = validated_data.pop('sns_detail_id')
#
#         instance = Account.objects.create(
#             own_group=own_group,
#             sns_group=sns_detail.group,
#             detail=sns_detail
#         )
#
#         return instance
#
#     def update(self, instance, validated_data):
#         pass
#
#
# class AccountDetailAddSerializer(AccountDetailSerializerForCreate):
#     class Meta:
#         model = AccountDetail
#         fields = '__all__'
#
#
# class AccountUpdateSerializer:
#     errors = {}
#     data = {}
#
#     user_id = None
#     group_serializer = None
#     detail_serializer = None
#
#     def __init__(self, user_id=None, data=empty, **kwargs) -> None:
#         account_group_data = data['account_group']
#         account_group_data['mwodeola_user'] = user_id
#         account_detail_data = data['details']
#
#         account_group_id = account_group_data['id']
#         detail_ids = []
#         for detail in account_detail_data:
#             detail_ids.append(detail['id'])
#
#         print(f'__init__(): account_group_id={account_group_id}')
#         print(f'__init__(): detail_ids={detail_ids}')
#
#         user = MwodeolaUser.objects.get(id=user_id)
#         qs_group = AccountGroup.objects\
#             .filter(mwodeola_user=user)\
#             .get(id=account_group_id)
#
#         print(f'__init__(): qs_group={qs_group}')
#
#         qs_details = AccountDetail.objects.filter(id__in=detail_ids)
#
#         print(f'__init__(): qs_details={qs_details}')
#
#         self.group_serializer = AccountGroupSerializerForUpdate(qs_group, data=account_group_data, **kwargs)
#         self.detail_serializer = AccountDetailSerializerForUpdate(qs_details, data=account_detail_data, many=True)
#
#     def is_valid(self):
#         valid = self.group_serializer.is_valid() and self.detail_serializer.is_valid()
#         self.errors['account_group_errors'] = self.group_serializer.errors
#         self.errors['details_errors'] = self.detail_serializer.errors
#         return valid
#
#     def save(self) -> None:
#         self.group_serializer.save()
#         self.detail_serializer.save()
#         self.data['account_group'] = self.group_serializer.data
#         self.data['details'] = self.detail_serializer.data
#
#
#
#
