from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('lead_id', 'full_name', 'company', 'source', 'estimated_deal_value', 'status', 'priority', 'assigned_to', 'next_followup_date')
    list_filter = ('status', 'priority', 'source', 'created_at')
    search_fields = ('lead_id', 'full_name', 'email', 'phone', 'company', 'interested_product')
    date_hierarchy = 'created_at'
    readonly_fields = ('lead_id', 'created_at', 'updated_at')

    fieldsets = (
        ('Prospect Identity', {
            'fields': ('lead_id', 'full_name', 'company', 'email', 'phone')
        }),
        ('Qualification & Pipeline', {
            'fields': ('source', 'interested_product', 'estimated_deal_value', 'status', 'priority', 'assigned_to', 'next_followup_date')
        }),
        ('Conversion & Notes', {
            'fields': ('converted_customer', 'lost_reason', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
