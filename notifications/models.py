from django.db import models
from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        TASK = 'task', 'Task'
        LEAD = 'lead', 'Lead'
        FOLLOWUP = 'followup', 'Follow-up'
        DEAL = 'deal', 'Deal'
        CUSTOMER = 'customer', 'Customer'
        SYSTEM = 'system', 'System'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, help_text="Internal URL for the object")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient}: {self.title}"


def create_notification(recipient, title, message, notification_type='system', link=''):
    """Helper to dispatch in-app notification to a user."""
    if not recipient:
        return None
    try:
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
    except Exception as e:
        print(f"Failed to create notification: {e}")
        return None
