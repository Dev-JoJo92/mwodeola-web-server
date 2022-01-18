from django.urls import path
from . import views

urlpatterns = [

    # GET(조회): (1) all
    # POST(생성): (1) with detail
    # PUT(수정): (1) with detail, (2) alone
    # DELETE(삭제)
    path('accounts/groups', views.AccountGroupView.as_view()),
    path('accounts/groups/favorite', views.AccountGroupFavoriteView.as_view()),
    path('accounts/groups/add/sns_detail', views.AccountGroupAddSnsDetailView.as_view()),  # POST

    # GET(조회): in group
    # POST(생성): add in group
    # PUT(수정): (1) with group, (2) alone
    # DELETE(삭제)
    path('accounts/details', views.AccountDetailView.as_view()),


    path('accounts/search', views.AccountSearchView.as_view()),

    # Test
    path('accounts/test', views.TestView.as_view()),
]
