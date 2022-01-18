import secrets

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings
from rest_framework import generics, status, exceptions
from rest_framework.views import APIView
from rest_framework.serializers import Serializer
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from Crypto import Random
from _mwodeola.cipher import AESCipher
import string
import random

from .models import AccountGroup, AccountDetail, Account
from .serializers_base import (
    AccountGroupSerializerForRead,
    AccountGroupSerializerForRead,
)
from .serializers import (
    GET_AccountGroupSerializer,
    POST_AccountGroupSerializer,
    PUT_AccountGroupSerializer,
    AccountGroupAddSnsDetailSerializer,
    SearchAccountGroupSerializer,
    AccountGroupFavoriteSerializer,
    GET_AccountDetailSerializer,
    POST_AccountDetailSerializer,
)


# Create your views here.
class TestView(APIView):
    def get(self, request):
        group_id = request.GET.get('group_id', None)
        if group_id is not None:
            group = AccountGroup.objects.get(id=group_id)
            accounts = Account.objects.filter(own_group=group_id)
            details = []
            for account in accounts:
                details.append(
                    AccountDetail.objects.get(id=account.detail_id))

            group_serializer = AccountGroupSerializerForRead(group)
            detail_serializer = AccountGroupSerializerForRead(details, many=True)
            group_dict = group_serializer.data
            detail_dict = detail_serializer.data
            result = {
                'account_group': group_dict,
                'details': detail_dict
            }
            return JsonResponse(result, safe=False, status=status.HTTP_200_OK)
        else:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        AccountGroup.objects.all().delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class BaseAccountView(APIView):
    user_id = None
    auth_prefix_len = len('Bearer ')
    default_errors = {}

    def check_permissions(self, request):
        super().check_permissions(request)
        try:
            authorization = request.META.get(api_settings.AUTH_HEADER_NAME)
            token_str = authorization[self.auth_prefix_len:]
            token = AccessToken(token_str)
            self.user_id = token.payload['user_id']
        except TokenError:
            pass

    @classmethod
    def post_general(cls, serializer):
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def put_general(cls, serializer):
        if serializer.is_valid():
            serializer.save()
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountGroupView(BaseAccountView):
    def get(self, request):
        groups = AccountGroup.objects.filter(mwodeola_user_id=self.user_id)
        serializer = GET_AccountGroupSerializer(groups, many=True)

        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = POST_AccountGroupSerializer(
            user_id=self.user_id, data=request.data)
        return super().post_general(serializer)

    def put(self, request):
        serializer = PUT_AccountGroupSerializer(user_id=self.user_id, data=request.data)
        return super().put_general(serializer)

    def delete(self, request):
        try:
            group_id = request.data['account_group_id']
        except KeyError as e:
            errors = {str(e): 'This is required field'}
            return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)

        group = AccountGroup.objects.filter(id=group_id)
        if group.exists():
            group.delete()
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)


class AccountGroupAddSnsDetailView(BaseAccountView):
    def post(self, request):
        serializer = AccountGroupAddSnsDetailSerializer(data=request.data)
        return super().post_general(serializer)


class AccountGroupFavoriteView(BaseAccountView):
    def put(self, request):
        serializer = AccountGroupFavoriteSerializer(data=request.data)
        return super().put_general(serializer)


class AccountDetailView(BaseAccountView):
    def get(self, request):
        group_id = request.GET.get('group_id', None)

        try:
            accounts = Account.objects.filter(own_group=group_id)
        except ValidationError as e:
            raise exceptions.ValidationError(e)

        details = []
        for account in accounts:
            details.append(account.detail)

        serializer = GET_AccountDetailSerializer(details, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = POST_AccountDetailSerializer(data=request.data)
        return super().post_general(serializer)

    def put(self, request):
        serializer = PUT_AccountGroupSerializer(user_id=self.user_id, data=request.data)
        return super().put_general(serializer)

    def delete(self, request):
        try:
            detail_id = request.data['account_detail_id']
        except KeyError as e:
            errors = {str(e): 'This is required field'}
            return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            detail = AccountDetail.objects.get(id=detail_id)
            accounts = Account.objects.filter(own_group=detail.group.id)
        except (ObjectDoesNotExist, ValidationError) as e:
            raise exceptions.ParseError(e)

        if accounts.count() == 1:
            accounts[0].own_group.delete()
        else:
            detail.delete()

        return HttpResponse(status=status.HTTP_200_OK)


class AccountSearchView(BaseAccountView):
    def get(self, request):
        group_name = request.GET.get('group_name', None)
        if group_name is not None:
            query_set = AccountGroup.objects.filter(group_name__contains=group_name)

        serializer = SearchAccountGroupSerializer(query_set, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


class ByteTest:
    BASE_DIR = settings.BASE_DIR
    SECRET_KEY_SHA = settings.SECRET_KEY
    SECRET_KEY_AES = settings.SECRET_KEY_AES

    def case_0(self):
        self._print(0, False)
        print(f'BASE_DIR={self.BASE_DIR}')
        print(f'SECRET_KEY_SHA={self.SECRET_KEY_SHA}')
        print(f'SECRET_KEY_AES={self.SECRET_KEY_AES}')
        self._print(0, True)

    # 1. secrets.token_bytes() 이용
    def case_1(self):
        self._print(1, False)
        random_key = secrets.token_bytes()
        print(f'random_key={random_key}')

        random_key_str_array = []

        for k in random_key:
            random_key_str_array.append(chr(k))

        print(f'random_key_str_array={random_key_str_array}')
        print(f'random_key_str_array={str(random_key_str_array)}')
        self._print(1, True)

    # 2. hex(ord(k)) 이용
    def case_2(self):
        self._print(2, False)
        secret_key = self.SECRET_KEY_SHA

        hex_list = []
        for k in secret_key:
            k_hex = hex(ord(k))
            hex_list.append(k_hex)

        print(hex_list)
        self._print(2, True)

    def case_3(self):
        self._print(3, False)
        token_bytes = secrets.token_bytes()
        print(f'token_bytes={token_bytes}')
        print(f'token_bytes={list(token_bytes)}')

        index = 0
        for token in token_bytes:
            c = chr(token)
            print(f'token[{index}] = ({token}, {c})')
            index += 1

        self._print(3, True)

    def case_4(self):
        self._print(4, False)
        token_hex = secrets.token_hex(32)
        print(f'secret_key_bytes={token_hex}')
        token_bytes = bytes(token_hex.encode())
        print(f'token_bytes={bytes(token_hex.encode())}')
        token_bytes_list = list(token_bytes)
        print(f'token_bytes_list={token_bytes_list}')

        index = 0
        for token in token_bytes_list:
            print(f'token[{index}] = ({token}, )')
            index += 1

        self._print(4, True)

    def case_5(self):
        self._print(5, False)
        keys = []
        for i in range(32):
            keys.append(
                random.choice(string.digits + string.ascii_letters + string.punctuation))

        secret_key = ''.join(keys)
        print(f'keys={keys}')
        print(f'secret_key={secret_key}')
        self._print(5, True)

    def case_final(self):
        self._print('FINAL', False)
        password = 'abcd1234'
        secret_key = self.SECRET_KEY_AES

        cipher = AESCipher(secret_key.encode())

        encode = cipher.encrypt(password)
        print(f'encode={encode}')

        decode = cipher.decrypt(encode)
        print(f'decode={decode}')
        self._print('FINAL', True)

    @classmethod
    def _print(cls, case, is_end: bool):
        if not is_end:
            print(f'★★★ TEST CASE {case}: start!! ★★★')
        else:
            print(f'★★★ TEST CASE {case}: start!! ★★★\n')
