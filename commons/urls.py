from django.urls import path
from . import views

urlpatterns = [
    path('api/data/all/count', views.DataAllCountView.as_view()),
]