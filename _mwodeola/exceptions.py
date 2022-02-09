from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class MyException(APIException):

    def __init__(self, message=None, code=None):
        super().__init__(None, None)
        self.detail = {
            "message": message,
            "code": code,
        }


class FieldException(MyException):

    def __init__(self, **kwargs):
        message = 'This is required field'
        code = 'field_error'
        super().__init__(message, code)
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail['detail'] = kwargs
        # if detail is not None:
        #     self.detail['detail'] = detail


class DuplicatedException(MyException):
    def __init__(self, **kwargs):
        message = 'This Field is duplicated'
        code = 'duplicated_field'
        super().__init__(message, code)
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail['detail'] = kwargs


class NotOwnerDataException(MyException):

    def __init__(self, **kwargs):
        message = 'You are not the owner of the data.'
        code = 'not_data_owner'
        super().__init__(message, code)
        self.status_code = status.HTTP_403_FORBIDDEN


def custom_exception_Handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response