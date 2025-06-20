from django.contrib import admin
from .models import User, Otp


class UserModelAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email', 'username', 'date_joined', 
        'is_active', 'is_staff', 'is_superuser'
    )
    list_filter = ('first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('id', 'first_name', 'last_name', 'email')
    ordering = ('id',)

admin.site.register(User, UserModelAdmin)


class OtpModelAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'purpose', 'code', 'is_verified', 'is_applied', 'is_deleted')
    list_filter = ('recipient', 'purpose', 'code', 'is_verified', 'is_applied', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('recipient', 'purpose', 'code', 'is_verified', 'is_applied', 'is_deleted')
    ordering = ('id',)

admin.site.register(Otp, OtpModelAdmin)