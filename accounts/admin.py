from django.contrib import admin
from .models import SNS, AccountGroup, AccountDetail, Account

# Register your models here.
admin.site.register(SNS)
admin.site.register(AccountGroup)
admin.site.register(AccountDetail)
admin.site.register(Account)
