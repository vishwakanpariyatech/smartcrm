from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'employee_id', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active', 'is_staff')
    search_fields = ('username', 'employee_id', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('employee_id',)

    fieldsets = UserAdmin.fieldsets + (
        ('CRM Roles & Info', {
            'fields': ('role', 'employee_id', 'department', 'phone', 'joining_date', 'profile_image', 'address', 'city', 'state')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CRM Roles & Info', {
            'fields': ('role', 'employee_id', 'department', 'phone', 'joining_date')
        }),
    )
