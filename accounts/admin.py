from django.contrib import admin
from .models import SNS, AccountGroup, AccountDetail, Account


class SNS_Admin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id',)


class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ('mwodeola_user', 'sns', 'group_name',
                    'app_package_name', 'web_url', 'icon_type', 'icon_image_url', 'is_favorite',
                    'created_at')
    list_filter = ['created_at']
    search_fields = ['group_name']
    readonly_fields = ('id', 'mwodeola_user')
    ordering = ('created_at',)


class AccountDetailAdmin(admin.ModelAdmin):
    list_display = ('mwodeola_user', 'group', 'user_id',
                    'user_password', 'user_password_pin', 'user_password_pattern',
                    'memo', 'views')
    search_fields = ['group']
    readonly_fields = ('id',)
    ordering = ('created_at',)

    def mwodeola_user(self, obj):
        return obj.group.mwodeola_user


class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'own_group', 'sns_group', 'detail', 'created_at')
    search_fields = ['own_group']
    readonly_fields = ('id', 'own_group', 'sns_group', 'detail', 'created_at')
    ordering = ('created_at',)

    def user(self, obj):
        return obj.own_group.mwodeola_user


# Register your models here.
admin.site.register(SNS, SNS_Admin)
admin.site.register(AccountGroup, AccountGroupAdmin)
admin.site.register(AccountDetail, AccountDetailAdmin)
admin.site.register(Account, AccountAdmin)
