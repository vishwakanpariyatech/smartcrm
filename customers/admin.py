from django.contrib import admin
from .models import Customer, CustomerNote


class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'full_name', 'company_name', 'email', 'phone', 'city', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'source', 'city', 'created_at')
    search_fields = ('customer_id', 'full_name', 'email', 'phone', 'company_name', 'city')
    date_hierarchy = 'created_at'
    inlines = [CustomerNoteInline]
    readonly_fields = ('customer_id', 'created_at', 'updated_at')

    fieldsets = (
        ('Customer Identification', {
            'fields': ('customer_id', 'full_name', 'company_name', 'email', 'phone')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('CRM Management', {
            'fields': ('source', 'status', 'assigned_to', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
