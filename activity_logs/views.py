from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ActivityLog
from accounts.models import User
from accounts.permissions import admin_required


@login_required
@admin_required
def activity_log_list(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')

    query = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    user_filter = request.GET.get('user', '')

    if query:
        logs = logs.filter(
            Q(object_repr__icontains=query) |
            Q(details__icontains=query) |
            Q(object_id__icontains=query)
        )

    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    if model_filter:
        logs = logs.filter(model_name=model_filter)

    if user_filter:
        logs = logs.filter(user_id=user_filter)

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    users = User.objects.filter(is_active=True).order_by('first_name')
    models_list = ['Customer', 'Lead', 'Deal', 'Task', 'Follow-up', 'Employee', 'User']

    context = {
        'page_obj': page_obj,
        'query': query,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'user_filter': user_filter,
        'users': users,
        'models_list': models_list,
    }
    return render(request, 'activity_logs/activity_log_list.html', context)
