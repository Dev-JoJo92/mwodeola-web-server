# import uuid
# from abc import ABCMeta, abstractmethod
# from collections import Counter, OrderedDict
# from django.core.exceptions import ObjectDoesNotExist, ValidationError
# from django.utils.translation import gettext_lazy as _
# from rest_framework import exceptions, serializers
# from rest_framework.fields import empty
#
# from .models import SNS, AccountGroup, AccountDetail, Account
# from .model_serializers_old import (
#     SnsSerializer,
#     AccountGroupSerializer,
#     AccountDetailSerializer,
#     AccountSerializer
# )
#
#
# class AccountGroupCreateWithNewDetailSerializer(serializers.Serializer):
#     account_group = AccountGroupSerializer()
#     detail = AccountDetailSerializer()
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
#         detail_data = validated_data.pop('detail')
#         new_detail = AccountDetail.objects.create(
#             group=new_group,
#             **detail_data
#         )
#
#         Account.objects.create(
#             own_group=new_group,
#             sns_group=None,
#             detail=new_detail
#         )
#         return {'results': 'Create Succeed!'}
#
#     def update(self, instance, validated_data):
#         pass
#
#
# class AccountGroupCreateWithSnsDetailSerializer(serializers.Serializer):
#     account_group = AccountGroupSerializer()
#     sns_detail_id = serializers.PrimaryKeyRelatedField(queryset=AccountDetail.objects.all())
#
#     def __init__(self, instance=None, data=empty, **kwargs):
#         data['account_group']['mwodeola_user'] = kwargs.pop('user_id')
#         super().__init__(instance, data, **kwargs)
#
#     def create(self, validated_data):
#         account_group_data = validated_data.pop('account_group')
#         own_group = AccountGroup.objects.create(
#             **account_group_data
#         )
#
#         # TODO: sns_detail 이 sns 그룹에 속했는지 확인하기.
#         sns_detail = validated_data.pop('sns_detail_id')
#         Account.objects.create(
#             own_group=own_group,
#             sns_group=sns_detail.group,
#             detail=sns_detail
#         )
#
#         return {'results': 'Create Succeed!'}
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
# class AccountDetailAddSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AccountDetail
#         fields = '__all__'
#
#     def create(self, validated_data):
#         new_detail = super().create(validated_data)
#         Account.objects.create(
#             own_group=new_detail.group,
#             detail=new_detail
#         )
#         return new_detail
#
