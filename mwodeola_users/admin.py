from django.contrib import admin
from .models import MwodeolaUser


class MwodeolaUserAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'email', 'phone_number',
                    'is_active', 'is_staff', 'is_superuser')
    list_filter = ['is_superuser']
    readonly_fields = ('id',)


# Register your models here.
admin.site.register(MwodeolaUser, MwodeolaUserAdmin)
