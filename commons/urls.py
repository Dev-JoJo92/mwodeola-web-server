from django.urls import path
from . import views

urlpatterns = [
    path('api/sns/info', views.SnsInfoView.as_view()),
    path('api/data/all/count', views.DataAllCountView.as_view()),
]