from django.contrib import admin
from .models import Deal


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('deal_id', 'title', 'customer', 'deal_value', 'stage', 'assigned_to', 'expected_closing_date', 'actual_closing_date')
    list_filter = ('stage', 'expected_closing_date', 'actual_closing_date')
    search_fields = ('deal_id', 'title', 'customer__full_name', 'customer__company_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('deal_id', 'created_at', 'updated_at')

    fieldsets = (
        ('Deal Particulars', {
            'fields': ('deal_id', 'title', 'customer', 'lead', 'deal_value', 'stage', 'assigned_to')
        }),
        ('Closing Timelines', {
            'fields': ('expected_closing_date', 'actual_closing_date')
        }),
        ('Commercial Terms', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
