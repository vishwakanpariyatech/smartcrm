from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'title', 'assigned_to', 'priority', 'status', 'due_date', 'completed_at', 'created_by')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('task_id', 'title', 'description')
    date_hierarchy = 'due_date'
    readonly_fields = ('task_id', 'created_at')
