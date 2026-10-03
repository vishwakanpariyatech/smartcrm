import calendar
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import FollowUp
from .forms import FollowUpForm, FollowUpCompleteForm
from customers.models import Customer
from leads.models import Lead
from accounts.models import User
from activity_logs.models import log_activity
from notifications.models import create_notification


def get_user_followups_qs(user):
    """Scoped FollowUp queryset based on role."""
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        return FollowUp.objects.all()
    return FollowUp.objects.filter(assigned_to=user)


@login_required
def followup_list(request):
    followups = get_user_followups_qs(request.user)

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    employee_filter = request.GET.get('employee', '')
    time_filter = request.GET.get('time_filter', '')

    today = timezone.now().date()

    if query:
        followups = followups.filter(
            Q(description__icontains=query) |
            Q(outcome__icontains=query) |
            Q(customer__full_name__icontains=query) |
            Q(lead__full_name__icontains=query)
        )

    if status_filter:
        followups = followups.filter(status=status_filter)

    if type_filter:
        followups = followups.filter(followup_type=type_filter)

    if employee_filter and (request.user.is_admin_role or request.user.is_manager_role):
        followups = followups.filter(assigned_to_id=employee_filter)

    if time_filter == 'upcoming':
        followups = followups.filter(followup_date__gte=today, status='Pending')
    elif time_filter == 'overdue':
        followups = followups.filter(followup_date__lt=today, status='Pending')
    elif time_filter == 'today':
        followups = followups.filter(followup_date=today)

    total_count = followups.count()
    pending_count = followups.filter(status='Pending').count()
    upcoming_count = followups.filter(followup_date__gte=today, status='Pending').count()
    overdue_count = followups.filter(followup_date__lt=today, status='Pending').count()

    paginator = Paginator(followups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    employees = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'employee_filter': employee_filter,
        'time_filter': time_filter,
        'types': FollowUp.Type.choices,
        'statuses': FollowUp.Status.choices,
        'employees': employees,
        'total_count': total_count,
        'pending_count': pending_count,
        'upcoming_count': upcoming_count,
        'overdue_count': overdue_count,
    }
    return render(request, 'followups/followup_list.html', context)


@login_required
def followup_calendar(request):
    """Monthly Calendar View for all scheduled follow-ups."""
    followups = get_user_followups_qs(request.user)

    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    # Calculate month calendar matrix
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    month_days = cal.monthdatescalendar(year, month)

    month_followups = followups.filter(
        followup_date__year=year,
        followup_date__month=month
    )

    # Group follow-ups by day
    followups_by_day = {}
    for f in month_followups:
        d_str = f.followup_date.strftime('%Y-%m-%d')
        if d_str not in followups_by_day:
            followups_by_day[d_str] = []
        followups_by_day[d_str].append(f)

    # Next / Prev month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = calendar.month_name[month]

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_days': month_days,
        'followups_by_day': followups_by_day,
        'today': now.date(),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    return render(request, 'followups/followup_calendar.html', context)


@login_required
def followup_create(request):
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
        form = FollowUpForm(request.POST, user=request.user)
        if form.is_valid():
            followup = form.save(commit=False)
            if request.user.is_employee_role and not followup.assigned_to:
                followup.assigned_to = request.user
            followup.save()

            target_name = followup.target_name
            log_activity(request.user, 'Created', 'Follow-up', followup.followup_id, f"{followup.followup_type} with {target_name}")
            if followup.assigned_to and followup.assigned_to != request.user:
                create_notification(
                    followup.assigned_to,
                    'Follow-up Scheduled',
                    f"Follow-up scheduled with {target_name} on {followup.followup_date}.",
                    'followup',
                    "/followups/"
                )
            messages.success(request, f"Follow-up ({followup.followup_id}) scheduled successfully.")
            return redirect('followups:list')
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = FollowUpForm(initial=initial, user=request.user)

    return render(request, 'followups/followup_form.html', {'form': form, 'title': 'Schedule New Follow-up'})


@login_required
def followup_edit(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)

    if request.user.is_employee_role and followup.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        form = FollowUpForm(request.POST, instance=followup, user=request.user)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'Updated', 'Follow-up', followup.followup_id, followup.target_name)
            messages.success(request, f"Follow-up ({followup.followup_id}) updated successfully.")
            return redirect('followups:list')
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = FollowUpForm(instance=followup, user=request.user)

    return render(request, 'followups/followup_form.html', {
        'form': form,
        'title': f'Edit Follow-up: {followup.followup_id}',
        'followup': followup
    })


@login_required
def followup_complete(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)

    if request.user.is_employee_role and followup.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        form = FollowUpCompleteForm(request.POST)
        if form.is_valid():
            followup.status = FollowUp.Status.COMPLETED
            followup.outcome = form.cleaned_data['outcome']
            followup.save()
            log_activity(request.user, 'Completed', 'Follow-up', followup.followup_id, followup.target_name, followup.outcome[:50])
            messages.success(request, f"Follow-up with {followup.target_name} completed and outcome recorded!")
        else:
            messages.error(request, "Outcome description is required.")

    return redirect(request.META.get('HTTP_REFERER', 'followups:list'))


@login_required
def followup_delete(request, pk):
    if request.method != 'POST':
        return redirect('followups:list')

    followup = get_object_or_404(FollowUp, pk=pk)
    if not (request.user.is_admin_role or request.user.is_manager_role or followup.assigned_to == request.user):
        raise PermissionDenied("Permission denied.")

    fid = followup.followup_id
    followup.delete()
    log_activity(request.user, 'Deleted', 'Follow-up', fid)
    messages.success(request, f"Follow-up ({fid}) has been removed.")
    return redirect('followups:list')
