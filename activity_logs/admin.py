from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr', 'details')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('object_repr', 'details', 'user__username', 'object_id')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 'details', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
