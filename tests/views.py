from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView

from . import serializers


# Create your views here.
class TestView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        meta = request.META
        ip_address = meta.get('REMOTE_ADDR', None)
        response = {
            'ip_address': ip_address,
            'request.meta': str(meta)
        }
        return JsonResponse(response, status=201)

    def post(self, request):
        serializer = serializers.TestSerializer(data=request.data)

        if serializer.is_valid():
            return JsonResponse(serializer.results, status=200)
        else:
            return JsonResponse(serializer.error_messages, status=serializer.error_status)
