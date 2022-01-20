from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView


# Create your views here.
class TestView(APIView):
    def get(self, request):
        meta = request.META
        ip_address = meta.get('REMOTE_ADDR', None)
        response = {
            'ip_address': ip_address,
            'request.meta': str(meta)
        }
        return JsonResponse(response, status=201)
