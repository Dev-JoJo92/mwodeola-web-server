from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import status, HTTP_HEADER_ENCODING
from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from _mwodeola.utils import get_random_secret_key_str
from mwodeola_users.models import MwodeolaUser
from .auth import get_raw_token, get_user_from_request_token
from .auth.authentications import JWTAuthenticationForRefresh
from .serializers_token import TokenRefreshSerializer, TokenBlacklistSerializer
from .serializers import (
    SignUpVerifyPhoneSerializer,
    SignUpVerifyEmailSerializer,
    SignUpSerializer,
    SignInVerifySerializer,
    SignInSerializer,
    SignInAutoSerializer,
    SignOutSerializer,
    WithdrawalSerializer,
    PasswordAuthSerializer,
    PasswordChangeSerializer,
    UserWakeUpSerializer,
)

AUTH_HEADER_TYPE_BYTES = set(
    h.encode(HTTP_HEADER_ENCODING)
    for h in AUTH_HEADER_TYPES
)

AUTH_LIMIT_DEFAULT = 5
AUTH_LIMIT = getattr(settings, "AUTH_LIMIT", AUTH_LIMIT_DEFAULT)


# Create your views here.
class BaseSignView(APIView):
    permission_classes = []
    authentication_classes = []

    serializer = None

    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

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
            return JsonResponse(serializer.results, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.err_messages, status=serializer.err_status)

    @classmethod
    def get_header(cls, request):
        header = request.META.get(simplejwt_api_settings.AUTH_HEADER_NAME)

        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)

        return header

    @classmethod
    def get_raw_token(cls, header):
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed(
                'Authorization header must contain two space-delimited values',
                code='bad_authorization_header',
            )

        return parts[1]


class SignUpVerifyPhoneView(BaseSignView):
    def post(self, request):
        self.serializer = SignUpVerifyPhoneSerializer(data=request.data)
        return super().post(request)


class SignUpVerifyEmailView(BaseSignView):
    def post(self, request):
        self.serializer = SignUpVerifyEmailSerializer(data=request.data)
        return super().post(request)


class SignUpView(BaseSignView):
    def post(self, request):
        self.serializer = SignUpSerializer(data=request.data)
        return super().post(request)


class SignInVerifyView(BaseSignView):
    def post(self, request):
        self.serializer = SignInVerifySerializer(data=request.data)
        return super().post(request)


#  TODO: Refresh 토큰이 아직 살아있는데 로그인 시도할 경우
#  TODO: 유저 phone_number 로 문자 발송 구현 예정.
class SignInView(BaseSignView):
    def post(self, request):
        self.serializer = SignInSerializer(data=request.data)
        return super().post(request)


class SignInAutoView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def get(self, request):
        user = get_user_from_request_token(request)
        refresh_token = get_raw_token(request)
        self.serializer = SignInAutoSerializer(user=user, refresh_token=refresh_token)
        return super().get(request)


class SignOutView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def put(self, request):
        raw_token = get_raw_token(request)
        data = {'refresh': raw_token}
        self.serializer = SignOutSerializer(data=data)
        return super().put(request)


# 회원 탈퇴
# 토큰(refresh) & 휴대폰 번호 & 비밀번호 인증 후 삭제.
# 추후 탈퇴 정책 만들기(7일 보관 등)
class WithdrawalView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def delete(self, request):
        user = get_user_from_request_token(request)
        self.serializer = WithdrawalSerializer(user, data=request.data)
        return super().delete(request)


class AuthFailedCountView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def get(self, request):
        result = {
            'auth_failed_count': request.user.count_auth_failed,
            'limit': AUTH_LIMIT
        }
        return JsonResponse(result, status=status.HTTP_200_OK)

    def post(self, request):
        auth_failed_count = request.data.get('auth_failed_count', None)
        if auth_failed_count is None:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        request.user.count_auth_failed = auth_failed_count

        if auth_failed_count >= AUTH_LIMIT:
            request.user.is_locked = True
            request.user.save()

            header = self.get_header(request)
            raw_token = self.get_raw_token(header).decode()
            data = {'refresh': raw_token}
            serializer = TokenBlacklistSerializer(data=data)
            serializer.is_valid()
            return HttpResponse(status=status.HTTP_200_OK)

        request.user.save()
        return HttpResponse(status=status.HTTP_200_OK)


class TokenRefreshView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def get(self, request):
        raw_token = get_raw_token(request)
        data = {'refresh': raw_token}
        self.serializer = TokenRefreshSerializer(data=data)
        return super().get(request)


class PasswordAuthView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def post(self, request):
        user = get_user_from_request_token(request)
        self.serializer = PasswordAuthSerializer(user, data=request.data)
        return super().post(request)


class PasswordChangeView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def put(self, request):
        user = get_user_from_request_token(request)
        self.serializer = PasswordChangeSerializer(user, data=request.data)
        return super().put(request)


class PasswordChangeForLostUser(BaseSignView):

    def put(self, request):
        return super().put(request)


class UserLockView(BaseSignView):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    authentication_classes = [JWTAuthenticationForRefresh]

    def post(self, request):
        header = self.get_header(request)
        raw_token = self.get_raw_token(header).decode()
        data = {'refresh': raw_token}
        serializer = TokenBlacklistSerializer(data=data)
        if serializer.is_valid():
            request.user.is_locked = True
            request.user.save()
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.data, status=status.HTTP_400_BAD_REQUEST)


# TODO: 인증 프로세스 추가 예정(휴대폰, 이메일 인증)
class UserWakeUpView(BaseSignView):
    def put(self, request):
        # self.serializer = UserWakeUpSerializer(data=request.data)
        return super().put(request)


# TODO: 인증 프로세스 추가 예정
# TODO: 1. 휴대폰 번호 인증
# TODO: 2. 이메일 인증
# TODO: 3. 계좌 인증
# TODO: 4. 퀴즈(개인정보가 유출되지 않는 선에서 해당 유저의 정보를 이용한 퀴즈)
class UserUnlockView(BaseSignView):
    def put(self, request):
        return super().put(request)


class UserChangePhoneNumberView(BaseSignView):
    def put(self, request):
        return super().put(request)
