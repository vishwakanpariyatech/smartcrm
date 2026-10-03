from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from accounts.models import User
from accounts.forms import EmployeeCreateForm, EmployeeUpdateForm
from accounts.permissions import manager_or_admin_required, admin_required
from activity_logs.models import log_activity
from sales.models import Deal
from leads.models import Lead
from tasks.models import Task
from followups.models import FollowUp


@login_required
@manager_or_admin_required
def employee_list(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')
    department_filter = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')

    employees = User.objects.all().order_by('-date_joined')

    if query:
        employees = employees.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(phone__icontains=query)
        )

    if role_filter:
        employees = employees.filter(role=role_filter)

    if department_filter:
        employees = employees.filter(department=department_filter)

    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)

    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'roles': User.Role.choices,
        'departments': User.Department.choices,
        'query': query,
        'role_filter': role_filter,
        'department_filter': department_filter,
        'status_filter': status_filter,
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
@admin_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            log_activity(request.user, 'Created', 'Employee', employee.id, employee.display_name, f"Role: {employee.role}")
            messages.success(request, f"Employee {employee.display_name} created successfully.")
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = EmployeeCreateForm()

    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add New Employee'})


@login_required
@admin_required
def employee_edit(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = EmployeeUpdateForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Updated', 'Employee', employee.id, employee.display_name)
            messages.success(request, f"Employee {employee.display_name} updated successfully.")
            return redirect('employees:detail', pk=employee.pk)
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = EmployeeUpdateForm(instance=employee)

    return render(request, 'employees/employee_form.html', {'form': form, 'title': f'Edit Employee: {employee.display_name}', 'employee': employee})


@login_required
@manager_or_admin_required
def employee_detail(request, pk):
    employee = get_object_or_404(User, pk=pk)

    # Performance Metrics
    total_sales_won = Deal.objects.filter(assigned_to=employee, stage='Won').aggregate(total=Sum('deal_value'))['total'] or 0
    deals_won_count = Deal.objects.filter(assigned_to=employee, stage='Won').count()
    leads_converted_count = Lead.objects.filter(assigned_to=employee, status='Converted').count()
    total_leads_count = Lead.objects.filter(assigned_to=employee).count()
    tasks_completed_count = Task.objects.filter(assigned_to=employee, status='Completed').count()
    total_tasks_count = Task.objects.filter(assigned_to=employee).count()
    followups_completed_count = FollowUp.objects.filter(assigned_to=employee, status='Completed').count()

    assigned_customers = employee.customers.all()[:5]
    assigned_leads = employee.leads.all()[:5]
    recent_tasks = employee.assigned_tasks.all()[:5]

    context = {
        'employee': employee,
        'total_sales_won': total_sales_won,
        'deals_won_count': deals_won_count,
        'leads_converted_count': leads_converted_count,
        'total_leads_count': total_leads_count,
        'tasks_completed_count': tasks_completed_count,
        'total_tasks_count': total_tasks_count,
        'followups_completed_count': followups_completed_count,
        'assigned_customers': assigned_customers,
        'assigned_leads': assigned_leads,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'employees/employee_detail.html', context)


@login_required
@admin_required
def employee_toggle_status(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if employee == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('employees:detail', pk=pk)

    employee.is_active = not employee.is_active
    employee.save()
    status_str = "activated" if employee.is_active else "deactivated"
    log_activity(request.user, f"Status changed to {status_str}", 'Employee', employee.id, employee.display_name)
    messages.success(request, f"Employee {employee.display_name} has been {status_str}.")
    return redirect('employees:detail', pk=pk)
