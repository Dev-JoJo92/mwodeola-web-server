from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import generics, status, exceptions
from rest_framework.views import APIView
from mwodeola_users.auth import get_raw_token, get_user_from_request_token

from .models import AccountGroup, AccountDetail
from . import serializers
from .mixins import AccountMixin


class BaseAPIView(APIView, AccountMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serializer = None
        # self.request_user = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.serializer = None
        # self.request_user = get_user_from_request_token(request)

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
        groups = self.get_all_account_group_by(request)
        serializer = serializers.AccountGroup_GET_Serializer(groups, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    def put(self, request):
        request.data['mwodeola_user'] = request.user.id
        account_group = self.get_account_group(request)
        self.serializer = serializers.AccountGroup_PUT_Serializer(account_group, data=request.data)
        return super().put(request)

    def delete(self, request):
        self.serializer = serializers.AccountGroup_DELETE_Serializer(user=request.user, data=request.data)
        return super().delete(request)


class AccountGroupFavoriteView(BaseAPIView):

    def put(self, request):
        self.serializer = serializers.AccountGroupFavorite_PUT_Serializer(user=request.user, data=request.data)
        return super().put(request)


class AccountGroupDetailView(BaseAPIView):

    def get(self, request):
        data = {'account_id': request.GET.get('account_id', None)}
        self.serializer = serializers.AccountGroupDetail_GET_Serializer(user=request.user, data=data)
        return super().get(request)

    def post(self, request):
        self.serializer = serializers.AccountGroupDetail_POST_Serializer(user=request.user, data=request.data)
        return super().post(request)

    def put(self, request):
        self.serializer = serializers.AccountGroupDetail_PUT_Serializer(user=request.user, data=request.data)
        return super().put(request)


class AccountGroupSnsDetailView(BaseAPIView):

    def post(self, request):
        self.serializer = serializers.AccountGroupSnsDetail_POST_Serializer(user=request.user,
                                                                            data=request.data)
        return super().post(request)

    def put(self, request):
        self.serializer = serializers.AccountGroupSnsDetail_PUT_Serializer(user=request.user,
                                                                           data=request.data)
        return super().put(request)

    def delete(self, request):
        self.serializer = serializers.AccountGroupSnsDetail_DELETE_Serializer(user=request.user, data=request.data)
        return super().delete(request)


class AccountGroupDetailAllView(BaseAPIView):

    def get(self, request):
        data = {'account_group_id': request.GET.get('group_id', None)}
        self.serializer = serializers.AccountGroupDetailAllSerializer(user=request.user, data=data)
        return super().get(request)


class AccountDetailView(BaseAPIView):

    def post(self, request):
        self.serializer = serializers.AccountDetail_POST_Serializer(user=request.user, data=request.data)
        return super().post(request)

    def delete(self, request):
        self.serializer = serializers.AccountDetail_DELETE_Serializer(user=request.user, data=request.data)
        return super().delete(request)


class AccountSearchGroupView(BaseAPIView):

    def get(self, request):
        group_name = request.GET.get('group_name', None)
        data = {'group_name': group_name}
        self.serializer = serializers.AccountSearchGroupSerializer(user=request.user, data=data)
        return super().get(request)


class AccountSearchDetailView(BaseAPIView):

    def get(self, request):
        user_id = request.GET.get('user_id', None)
        data = {'user_id': user_id}
        self.serializer = serializers.AccountSearchDetailSerializer(user=request.user, data=data)
        return super().get(request)


class AccountForAutofillServiceView(BaseAPIView):

    def get(self, request):
        app_package_name = request.GET.get('app_package_name', None)
        data = {'app_package_name': app_package_name}
        self.serializer = serializers.GET_AccountForAutofillServiceSerializer(user=request.user, data=data)
        return super().get(request)

    def post(self, request):
        self.serializer = serializers.POST_AccountForAutofillServiceSerializer(user=request.user, data=request.data)
        return super().post(request)

