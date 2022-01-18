# from rest_framework import serializers
# from .models import AccountGroup, AccountDetail, Account, SNS
# from mwodeola_users.serializers import MwodeolaUserSerializer
# from mwodeola_users.models import MwodeolaUser
#
#
# class SnsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SNS
#         fields = '__all__'
#
#
# class AccountGroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AccountGroup
#         fields = '__all__'
#
#     def to_representation(self, instance):
#         self.fields['mwodeola_user'] = MwodeolaUser()
#         self.fields['sns'] = SnsSerializer()
#         super(AccountGroupSerializer, self).to_representation(instance)
#
#
# class AccountDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AccountDetail
#         fields = '__all__'
#         read_only_fields = ['group']
#
#     def to_representation(self, instance):
#         self.fields['group'] = AccountGroupSerializer()
#         super(AccountDetailSerializer, self).to_representation(instance)
#
#
# class AccountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Account
#         fields = '__all__'
#
#     def to_representation(self, instance):
#         self.fields['own_group'] = AccountGroupSerializer()
#         self.fields['sns_group'] = AccountGroupSerializer()
#         self.fields['detail'] = AccountDetailSerializer()
#         super(AccountSerializer, self).to_representation(instance)
