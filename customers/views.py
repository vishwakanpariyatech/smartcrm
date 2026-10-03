from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import Customer, CustomerNote
from .forms import CustomerForm, CustomerNoteForm
from accounts.models import User
from activity_logs.models import log_activity, ActivityLog
from notifications.models import create_notification


def get_user_customers_qs(user):
    """Return Customer queryset scoped to current user's role permissions."""
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        return Customer.objects.all()
    return Customer.objects.filter(assigned_to=user)


@login_required
def customer_list(request):
    customers = get_user_customers_qs(request.user)

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    city_filter = request.GET.get('city', '')
    employee_filter = request.GET.get('employee', '')
    sort_by = request.GET.get('sort', '-created_at')

    if query:
        customers = customers.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(company_name__icontains=query) |
            Q(customer_id__icontains=query)
        )

    if status_filter:
        customers = customers.filter(status=status_filter)

    if city_filter:
        customers = customers.filter(city__icontains=city_filter)

    if employee_filter and (request.user.is_admin_role or request.user.is_manager_role):
        customers = customers.filter(assigned_to_id=employee_filter)

    allowed_sorts = ['full_name', '-full_name', 'company_name', '-company_name', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        customers = customers.order_by(sort_by)
    else:
        customers = customers.order_by('-created_at')

    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    employees = User.objects.filter(is_active=True).order_by('first_name')
    cities = Customer.objects.values_list('city', flat=True).distinct().exclude(city='')

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'city_filter': city_filter,
        'employee_filter': employee_filter,
        'sort_by': sort_by,
        'employees': employees,
        'cities': cities,
        'statuses': Customer.Status.choices,
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST, user=request.user)
        if form.is_valid():
            customer = form.save(commit=False)
            if request.user.is_employee_role and not customer.assigned_to:
                customer.assigned_to = request.user
            customer.save()

            log_activity(request.user, 'Created', 'Customer', customer.customer_id, customer.full_name)
            if customer.assigned_to and customer.assigned_to != request.user:
                create_notification(
                    customer.assigned_to,
                    'Customer Assigned',
                    f"Customer {customer.full_name} has been assigned to you by {request.user.display_name}.",
                    'customer',
                    f"/customers/{customer.pk}/"
                )
            messages.success(request, f"Customer {customer.full_name} ({customer.customer_id}) created successfully.")
            return redirect('customers:detail', pk=customer.pk)
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = CustomerForm(user=request.user)

    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Add New Customer'})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    # Server-side RBAC validation
    if request.user.is_employee_role and customer.assigned_to != request.user:
        messages.error(request, "You do not have permission to view this customer.")
        raise PermissionDenied("Access to this customer record is restricted.")

    deals = customer.deals.all().order_by('-created_at')
    followups = customer.followups.all().order_by('-followup_date')
    tasks = customer.tasks.all().order_by('-due_date')
    notes = customer.customer_notes.all()
    note_form = CustomerNoteForm()

    # Timeline of activity
    recent_activities = ActivityLog.objects.filter(
        model_name='Customer', object_id=customer.customer_id
    ).order_by('-timestamp')[:10]

    context = {
        'customer': customer,
        'deals': deals,
        'followups': followups,
        'tasks': tasks,
        'notes': notes,
        'note_form': note_form,
        'recent_activities': recent_activities,
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.user.is_employee_role and customer.assigned_to != request.user:
        messages.error(request, "You do not have permission to edit this customer.")
        raise PermissionDenied("Access to modify this customer record is restricted.")

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer, user=request.user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Updated', 'Customer', customer.customer_id, customer.full_name)
            messages.success(request, f"Customer {customer.full_name} updated successfully.")
            return redirect('customers:detail', pk=customer.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = CustomerForm(instance=customer, user=request.user)

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': f'Edit Customer: {customer.full_name}',
        'customer': customer
    })


@login_required
def customer_delete(request, pk):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('customers:list')

    customer = get_object_or_404(Customer, pk=pk)

    # Deletion is restricted to Admin & Manager
    if not (request.user.is_admin_role or request.user.is_manager_role):
        messages.error(request, "Only Managers and Admins can delete customer records.")
        raise PermissionDenied("Customer deletion permission denied.")

    cust_name = customer.full_name
    cust_id = customer.customer_id
    customer.delete()
    log_activity(request.user, 'Deleted', 'Customer', cust_id, cust_name)
    messages.success(request, f"Customer {cust_name} ({cust_id}) has been deleted.")
    return redirect('customers:list')


@login_required
def add_customer_note(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.user.is_employee_role and customer.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        form = CustomerNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.customer = customer
            note.author = request.user
            note.save()
            log_activity(request.user, 'Added Note', 'Customer', customer.customer_id, customer.full_name, note.content[:50])
            messages.success(request, "Note added successfully.")

    return redirect('customers:detail', pk=pk)
