from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import generics, status, exceptions
from rest_framework.views import APIView
from mwodeola_users.auth import get_raw_token, get_user_from_request_token

from .models import AccountGroup, AccountDetail
from . import serializers


class BaseAPIView(APIView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serializer = None
        self.request_user = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        print('initial()')
        self.serializer = None
        self.request_user = get_user_from_request_token(request)

    def get(self, request):
        return self.response(request)

    def post(self, request):
        return self.response(request)

    def put(self, request):
        return self.response(request)

    def delete(self, request):
        return self.response(request)

    def response(self, request):
        if self.serializer is None:
            return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        serializer = self.serializer

        if serializer.is_valid():
            if request.method == 'POST' or request.method == 'PUT':
                serializer.save()
            if request.method == 'DELETE':
                serializer.delete()
            return JsonResponse(serializer.results, safe=False, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.err_messages, status=serializer.err_status)


class AccountGroupView(BaseAPIView):

    def get(self, request):
        groups = AccountGroup.objects.filter(mwodeola_user=self.request_user)
        serializer = serializers.AccountGroup_GET_Serializer(groups, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def put(self, request):
        self.serializer = None
        return super().put(request)

    def delete(self, request):
        self.serializer = serializers.AccountGroup_DELETE_Serializer(user=self.request_user, data=request.data)
        return super().delete(request)


class AccountGroupFavoriteView(BaseAPIView):

    def put(self, request):
        self.serializer = serializers.AccountGroupFavorite_PUT_Serializer(user=self.request_user, data=request.data)
        return super().put(request)


class AccountGroupDetailView(BaseAPIView):

    def get(self, request):
        data = {'account_detail_id': request.GET.get('id', None)}
        self.serializer = serializers.AccountGroupDetail_GET_Serializer(user=self.request_user, data=data)
        return super().get(request)

    def post(self, request):
        self.serializer = serializers.AccountGroupDetail_POST_Serializer(user=self.request_user, data=request.data)
        return super().post(request)

    def put(self, request):
        self.serializer = serializers.AccountGroupDetail_PUT_Serializer(user=self.request_user, data=request.data)
        return super().put(request)


class AccountGroupSnsDetailView(BaseAPIView):

    def post(self, request):
        self.serializer = serializers.AccountGroupSnsDetail_POST_Serializer(user=self.request_user,
                                                                            data=request.data)
        return super().post(request)

    def delete(self, request):
        self.serializer = serializers.AccountGroupSnsDetail_DELETE_Serializer(user=self.request_user, data=request.data)
        return super().delete(request)


class AccountGroupDetailAllView(BaseAPIView):

    def get(self, request):
        data = {'account_group_id': request.GET.get('group_id', None)}
        self.serializer = serializers.AccountGroupDetailAllSerializer(user=self.request_user, data=data)
        return super().get(request)


class AccountDetailView(BaseAPIView):

    def post(self, request):
        self.serializer = serializers.AccountDetail_POST_Serializer(data=request.data)
        return super().post(request)

    def delete(self, request):
        self.serializer = serializers.AccountDetail_DELETE_Serializer(user=self.request_user, data=request.data)
        return super().delete(request)


class AccountSearchGroupView(BaseAPIView):

    def get(self, request):
        group_name = request.GET.get('name', None)
        query_set = {}
        if group_name is not None:
            query_set = AccountGroup.objects.filter(group_name__contains=group_name)

        serializer = serializers.AccountSearchGroupSerializer(query_set, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


class AccountSearchDetailView(BaseAPIView):

    def get(self, request):
        user_id = request.GET.get('user_id', None)
        query_set = {}
        if user_id is not None:
            query_set = AccountDetail.objects.filter(user_id__contains=user_id)

        serializer = serializers.AccountSearchDetailSerializer(query_set, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

