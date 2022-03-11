from django.urls import path
from . import views

urlpatterns = [

    # GET: all
    # PUT: update only group
    # DELETE: delete group
    path('account/group', views.AccountGroupView.as_view()),

    # PUT: update favorite
    path('account/group/favorite', views.AccountGroupFavoriteView.as_view()),

    # GET: group and detail
    # POST: create new group and new detail
    # PUT: update group and detail
    path('account/group/detail', views.AccountGroupDetailView.as_view()),

    # GET: all details in group
    path('account/group/detail/all', views.AccountGroupDetailAllView.as_view()),

    # POST: create new group and add sns_detail
    # PUT: add sns_detail in group
    # DELETE: disconnect sns_detail
    path('account/group/sns_detail', views.AccountGroupSnsDetailView.as_view()),

    # POST: add new detail in group
    # DELETE: delete detail
    path('account/detail', views.AccountDetailView.as_view()),

    # GET: account/search/group?group_name=
    path('account/search/group', views.AccountSearchGroupView.as_view()),
    # GET: account/search/group?user_id=
    path('account/search/detail', views.AccountSearchDetailView.as_view()),

    # GET: get all user_ids
    path('account/user_id/all', views.AccountUserIdsView.as_view()),

    # GET: account/for_autofill_service?app_package_name=
    # POST: create new account for autofill-service.
    #       but, already exists based on app_package_name, it updates the existing data.
    path('account/for_autofill_service', views.AccountForAutofillServiceView.as_view()),


]
