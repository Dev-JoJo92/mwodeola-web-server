from django.urls import path
from . import views

urlpatterns = [
    path('users/sign_up', views.sign_up),
    path('users/sign_in', views.sign_in),
    path('users/sign_out', views.sign_out),
]
