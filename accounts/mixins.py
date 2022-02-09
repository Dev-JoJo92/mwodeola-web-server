from django.core.exceptions import ObjectDoesNotExist, ValidationError

from _mwodeola import exceptions
from .models import SNS, AccountGroup, AccountDetail, Account


class AccountMixin:

    def get_all_account_group_by(self, request):
        return AccountGroup.objects.filter(mwodeola_user=request.user)

    def get_account_group(self, request):
        account_group_id = request.data.get('id', None)

        if account_group_id is None:
            raise exceptions.FieldException(id='required field')

        try:
            account_group = AccountGroup.objects.get(id=account_group_id)
        except ValidationError as e:
            raise exceptions.FieldException(id=e)
        except ObjectDoesNotExist as e:
            raise exceptions.FieldException(id=e.args)

        if not self._match_user_account_group(request.user, account_group):
            raise exceptions.NotOwnerDataException()

        return account_group

    @classmethod
    def _match_user_account_group(cls, user, account_group) -> bool:
        return user.id == account_group.mwodeola_user.id

