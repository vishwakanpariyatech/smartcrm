from .models import Notification

def notification_context(request):
    """Context processor providing unread notifications and count to all views."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifications,
        }
    return {
        'unread_notifications_count': 0,
        'latest_notifications': [],
    }
