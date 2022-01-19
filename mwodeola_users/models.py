from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import MwodeolaUserManager
import uuid


class MwodeolaUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_name = models.CharField(
        max_length=50,
        null=False,
        blank=False
    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        null=False,
        blank=False
    )
    phone_number = models.CharField(
        verbose_name='phone number',
        max_length=16,
        unique=True,
        null=False,
        blank=False
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    secret_key = models.CharField(max_length=32, null=True, blank=False, default=None)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['user_name', 'email', 'password']

    objects = MwodeolaUserManager()

    def __str__(self):
        if self.is_superuser:
            return f'[Admin] {self.user_name}({self.phone_number})'
        else:
            return f'{self.user_name}({self.phone_number})'

    class Meta:
        db_table = "mwodeola_user"
