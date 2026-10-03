from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=50, help_text="e.g. Created, Updated, Converted, Completed")
    model_name = models.CharField(max_length=50, help_text="e.g. Customer, Lead, Task, Deal")
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        user_str = self.user.display_name if self.user else "System"
        return f"[{self.timestamp.strftime('%d-%m-%Y %H:%M')}] {user_str} {self.action} {self.model_name}: {self.object_repr}"


def log_activity(user, action, model_name, object_id='', object_repr='', details=''):
    """Helper utility to log significant CRM actions across apps."""
    try:
        user_instance = user if getattr(user, 'is_authenticated', False) else None
        return ActivityLog.objects.create(
            user=user_instance,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            object_repr=str(object_repr)[:250],
            details=str(details)
        )
    except Exception as e:
        # Fallback so logging failure never blocks primary business logic
        print(f"Failed to log activity: {e}")
        return None
