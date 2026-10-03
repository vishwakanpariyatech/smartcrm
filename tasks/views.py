from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Task
from .forms import TaskForm
from customers.models import Customer
from leads.models import Lead
from accounts.models import User
from activity_logs.models import log_activity
from notifications.models import create_notification


def get_user_tasks_qs(user):
    """Scoped Task queryset based on user role."""
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        return Task.objects.all()
    return Task.objects.filter(Q(assigned_to=user) | Q(created_by=user))


@login_required
def task_list(request):
    tasks = get_user_tasks_qs(request.user)

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    employee_filter = request.GET.get('employee', '')
    overdue_only = request.GET.get('overdue', '')

    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(task_id__icontains=query) |
            Q(description__icontains=query)
        )

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if employee_filter and (request.user.is_admin_role or request.user.is_manager_role):
        tasks = tasks.filter(assigned_to_id=employee_filter)

    today = timezone.now().date()
    if overdue_only == 'true':
        tasks = tasks.filter(due_date__lt=today).exclude(status='Completed')

    # Metric counts
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='Pending').count()
    in_progress_tasks = tasks.filter(status='In Progress').count()
    completed_tasks = tasks.filter(status='Completed').count()
    overdue_count = tasks.filter(due_date__lt=today).exclude(status='Completed').count()

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    employees = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'employee_filter': employee_filter,
        'overdue_only': overdue_only,
        'priorities': Task.Priority.choices,
        'statuses': Task.Status.choices,
        'employees': employees,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_count': overdue_count,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    initial = {}
    customer_id = request.GET.get('customer')
    lead_id = request.GET.get('lead')

    if customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        initial['customer'] = customer
        initial['assigned_to'] = customer.assigned_to
    if lead_id:
        lead = get_object_or_404(Lead, pk=lead_id)
        initial['lead'] = lead
        initial['assigned_to'] = lead.assigned_to

    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            if request.user.is_employee_role and not task.assigned_to:
                task.assigned_to = request.user
            task.save()

            log_activity(request.user, 'Created', 'Task', task.task_id, task.title)
            if task.assigned_to and task.assigned_to != request.user:
                create_notification(
                    task.assigned_to,
                    'New Task Assigned',
                    f"Task '{task.title}' assigned to you by {request.user.display_name}. Due: {task.due_date}",
                    'task',
                    f"/tasks/{task.pk}/"
                )
            messages.success(request, f"Task '{task.title}' ({task.task_id}) created successfully.")
            return redirect('tasks:detail', pk=task.pk)
        else:
            messages.error(request, "Please fix form errors.")
    else:
        form = TaskForm(initial=initial, user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create New Task'})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.user.is_employee_role and task.assigned_to != request.user and task.created_by != request.user:
        raise PermissionDenied("Access to this task is restricted.")

    context = {'task': task}
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.user.is_employee_role and task.assigned_to != request.user and task.created_by != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Updated', 'Task', task.task_id, task.title)
            messages.success(request, f"Task '{task.title}' updated successfully.")
            return redirect('tasks:detail', pk=task.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': f'Edit Task: {task.title}',
        'task': task
    })


@login_required
def task_delete(request, pk):
    if request.method != 'POST':
        return redirect('tasks:list')

    task = get_object_or_404(Task, pk=pk)
    if not (request.user.is_admin_role or request.user.is_manager_role or task.created_by == request.user):
        raise PermissionDenied("You do not have permission to delete this task.")

    title = task.title
    tid = task.task_id
    task.delete()
    log_activity(request.user, 'Deleted', 'Task', tid, title)
    messages.success(request, f"Task '{title}' ({tid}) has been deleted.")
    return redirect('tasks:list')


@login_required
def task_toggle_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.user.is_employee_role and task.assigned_to != request.user and task.created_by != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        if task.status == Task.Status.COMPLETED:
            task.status = Task.Status.PENDING
            task.completed_at = None
            msg = f"Task '{task.title}' marked as Pending."
            log_activity(request.user, 'Marked Pending', 'Task', task.task_id, task.title)
        else:
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            msg = f"Task '{task.title}' marked as Completed!"
            log_activity(request.user, 'Completed', 'Task', task.task_id, task.title)

        task.save()
        messages.success(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'tasks:list'))
