from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from mwodeola_users.auth import get_raw_token, get_user_from_request_token
from mwodeola_users.models import MwodeolaUser


class TokenAnalyzeView(APIView):
    def get(self, request):
        request_user = get_user_from_request_token(request)

        if not request_user.is_superuser or not request_user.is_staff:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)

        # token_ids_of_users = []
        #
        # users = MwodeolaUser.objects.all()
        # for user in users:
        #     token_ids_of_users.append(
        #         OutstandingToken.objects.filter(user_id=user.id).id
        #     )
        #
        # for token_ids in token_ids_of_users:
        #     blacklist_of_users = BlacklistedToken.objects.filter(token_id__in=token_ids)

        return JsonResponse({}, status=status.HTTP_200_OK)


token_analyze = TokenAnalyzeView.as_view()
