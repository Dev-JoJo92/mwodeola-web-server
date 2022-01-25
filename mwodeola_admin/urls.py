from django.urls import path
from . import views


urlpatterns = [
    path('mwodeola/admin/token/analyze', views.token_analyze),
]
