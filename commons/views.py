from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from mwodeola_users.auth import get_raw_token, get_user_from_request_token
from accounts.models import SNS, AccountGroup, AccountDetail, Account

from .serializers import (
    SnsSerializer
)


# Create your views here.
class BaseAPIView(APIView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serializer = None
        self.request_user = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
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


class SnsInfoView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        sns_qs = SNS.objects.all()
        serializer = SnsSerializer(sns_qs, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


class DataAllCountView(BaseAPIView):
    def get(self, request):
        groups = AccountGroup.objects.filter(mwodeola_user=self.request_user)
        group_count = len(groups)
        account_count = Account.objects.filter(own_group__in=groups).count()
        results = {
            'account': {
                'group_count': group_count,
                'detail_count': account_count
            },
            'credit_card': {

            }
        }
        return JsonResponse(results, status=status.HTTP_200_OK)
