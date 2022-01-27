from django.urls import path
from . import views

urlpatterns = [
    path('users/sign_up/verify', views.SignUpVerifyView.as_view()),
    path('users/sign_up', views.SignUpView.as_view()),
    path('users/sign_in', views.SignInView.as_view()),
    path('users/sign_in/auto', views.SignInAutoView.as_view()),
    path('users/sign_out', views.SignOutView.as_view()),
    path('users/withdrawal', views.WithdrawalView.as_view()),

    # Refresh Token
    path('users/token/refresh', views.TokenRefreshView.as_view()),
    # Password Authentication
    path('users/password/auth', views.PasswordAuthView.as_view()),
    # Password Change
    path('users/password/change', views.PasswordChangeView.as_view()),
    # Password Change for lost user
    # path('users/password/change_for_loss', views.PasswordChangeForLostUser.as_view()),

    # 계정 휴면 해제
    # path('users/wake_up', views.UserWakeUpView.as_view()),
    # 계정 잠금 해제
    # path('users/unlock', views.UserUnlockView.as_view()),
    # 휴대폰 번호 변경
    # path('users/phone_change', views.UserChangePhoneNumberView.as_view()),
    # 멀티 폰 서비스
    # path('users/')
]
