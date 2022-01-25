from django.urls import path
from . import views

urlpatterns = [
    path('users/sign_up/verify', views.sign_up_verify),
    path('users/sign_up', views.sign_up),
    path('users/sign_in', views.sign_in),
    path('users/auto_sign_in', views.auto_sign_in),
    path('users/sign_out', views.sign_out),
    path('users/withdrawal', views.withdrawal),

    # Password Authentication
    path('users/password/auth', views.password_auth),
    # Password Change
    path('users/password/change', views.password_change),
    # Refresh Token
    path('users/token/refresh', views.token_refresh),
]
