from django.urls import path
from . import views

urlpatterns = [
    # path('token/obtain_pair', views.token_obtain_pair),
    # path('token/verify', views.token_verify),
    path('token/refresh', views.token_refresh),
    path('token/rotation', views.token_rotation),
]
