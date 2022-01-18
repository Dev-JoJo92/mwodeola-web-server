from .models import AccountGroup
from django.core.exceptions import ObjectDoesNotExist


def is_sns_group(group_id: int) -> bool:
    try:
        group = AccountGroup.objects.get(id=group_id)
    except ObjectDoesNotExist:
        return False

    return group.sns is not None
