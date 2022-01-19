from django.contrib import admin
from .models import SNS, AccountGroup, AccountDetail, Account


class SNS_Admin(admin.ModelAdmin):
    list_display = ('id', 'name')


class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ('mwodeola_user', 'sns', 'group_name',
                    'app_package_name', 'web_url', 'icon_type', 'icon_image_url', 'is_favorite',
                    'created_at')
    list_filter = ['created_at']
    search_fields = ['group_name']


class AccountDetailAdmin(admin.ModelAdmin):
    list_display = ('group', 'user_id',
                    'user_password', 'user_password_pin', 'user_password_pattern',
                    'memo', 'views')
    search_fields = ['group']


class AccountAdmin(admin.ModelAdmin):
    list_display = ('own_group', 'sns_group', 'detail')
    search_fields = ['own_group']


# Register your models here.
admin.site.register(SNS, SNS_Admin)
admin.site.register(AccountGroup, AccountGroupAdmin)
admin.site.register(AccountDetail, AccountDetailAdmin)
admin.site.register(Account, AccountAdmin)
