from django.contrib import admin
from .models import FollowUp


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('followup_id', 'target_name', 'followup_type', 'assigned_to', 'followup_date', 'followup_time', 'status')
    list_filter = ('status', 'followup_type', 'followup_date')
    search_fields = ('followup_id', 'description', 'outcome')
    date_hierarchy = 'followup_date'
    readonly_fields = ('followup_id', 'created_at')
