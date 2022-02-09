from rest_framework import exceptions, serializers, status
from rest_framework.fields import empty

from accounts.models import SNS


class BaseModelSerializer(serializers.ModelSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.results = {}
        self.err_messages = {}
        self.err_status = status.HTTP_400_BAD_REQUEST

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            self.err_messages['message'] = 'Field error'
            self.err_messages['code'] = 'field_error'
            self.err_messages['detail'] = self.errors
            return False
        else:
            self.results = self.data
            return True


class SnsSerializer(BaseModelSerializer):
    class Meta:
        model = SNS
        fields = '__all__'

