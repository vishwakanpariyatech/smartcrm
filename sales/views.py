from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Deal
from .forms import DealForm
from customers.models import Customer
from leads.models import Lead
from accounts.models import User
from activity_logs.models import log_activity, ActivityLog
from notifications.models import create_notification


def get_user_deals_qs(user):
    """Scoped Deal queryset based on user role."""
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        return Deal.objects.all()
    return Deal.objects.filter(assigned_to=user)


@login_required
def deal_list(request):
    deals = get_user_deals_qs(request.user)

    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '')
    employee_filter = request.GET.get('employee', '')

    if query:
        deals = deals.filter(
            Q(title__icontains=query) |
            Q(deal_id__icontains=query) |
            Q(customer__full_name__icontains=query) |
            Q(customer__company_name__icontains=query)
        )

    if stage_filter:
        deals = deals.filter(stage=stage_filter)

    if employee_filter and (request.user.is_admin_role or request.user.is_manager_role):
        deals = deals.filter(assigned_to_id=employee_filter)

    # Revenue calculations ensuring precision & preventing double-counting
    total_deals = deals.count()
    won_deals = deals.filter(stage='Won')
    total_won_revenue = won_deals.aggregate(v=Sum('deal_value'))['v'] or 0
    won_count = won_deals.count()
    pipeline_value = deals.exclude(stage__in=['Won', 'Lost']).aggregate(v=Sum('deal_value'))['v'] or 0
    win_rate = round((won_count / total_deals * 100), 1) if total_deals > 0 else 0

    paginator = Paginator(deals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    employees = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'page_obj': page_obj,
        'query': query,
        'stage_filter': stage_filter,
        'employee_filter': employee_filter,
        'stages': Deal.Stage.choices,
        'employees': employees,
        'total_won_revenue': total_won_revenue,
        'won_count': won_count,
        'pipeline_value': pipeline_value,
        'win_rate': win_rate,
    }
    return render(request, 'sales/deal_list.html', context)


@login_required
def deal_create(request):
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
        initial['deal_value'] = lead.estimated_deal_value
        initial['assigned_to'] = lead.assigned_to

    if request.method == 'POST':
        form = DealForm(request.POST, user=request.user)
        if form.is_valid():
            deal = form.save(commit=False)
            if request.user.is_employee_role and not deal.assigned_to:
                deal.assigned_to = request.user
            deal.save()

            log_activity(request.user, 'Created', 'Deal', deal.deal_id, deal.title, f"Value: ₹{deal.deal_value}")
            if deal.assigned_to and deal.assigned_to != request.user:
                create_notification(
                    deal.assigned_to,
                    'Deal Assigned',
                    f"Deal '{deal.title}' (₹{deal.deal_value}) has been assigned to you.",
                    'deal',
                    f"/sales/{deal.pk}/"
                )
            messages.success(request, f"Deal '{deal.title}' ({deal.deal_id}) created successfully.")
            return redirect('sales:detail', pk=deal.pk)
        else:
            messages.error(request, "Please fix the form errors.")
    else:
        form = DealForm(initial=initial, user=request.user)

    return render(request, 'sales/deal_form.html', {'form': form, 'title': 'Create New Deal'})


@login_required
def deal_detail(request, pk):
    deal = get_object_or_404(Deal, pk=pk)

    if request.user.is_employee_role and deal.assigned_to != request.user:
        raise PermissionDenied("Access to this sales deal is restricted.")

    recent_activities = ActivityLog.objects.filter(
        model_name='Deal', object_id=deal.deal_id
    ).order_by('-timestamp')[:10]

    context = {
        'deal': deal,
        'recent_activities': recent_activities,
    }
    return render(request, 'sales/deal_detail.html', context)


@login_required
def deal_edit(request, pk):
    deal = get_object_or_404(Deal, pk=pk)

    if request.user.is_employee_role and deal.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    old_stage = deal.stage
    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal, user=request.user)
        if form.is_valid():
            updated_deal = form.save()
            if updated_deal.stage != old_stage:
                log_activity(request.user, f"Stage updated: {old_stage} -> {updated_deal.stage}", 'Deal', deal.deal_id, deal.title)
            else:
                log_activity(request.user, 'Updated', 'Deal', deal.deal_id, deal.title)
            messages.success(request, f"Deal '{deal.title}' updated successfully.")
            return redirect('sales:detail', pk=deal.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = DealForm(instance=deal, user=request.user)

    return render(request, 'sales/deal_form.html', {
        'form': form,
        'title': f'Edit Deal: {deal.title}',
        'deal': deal
    })


@login_required
def deal_delete(request, pk):
    if request.method != 'POST':
        return redirect('sales:list')

    deal = get_object_or_404(Deal, pk=pk)
    if not (request.user.is_admin_role or request.user.is_manager_role):
        raise PermissionDenied("Only Managers and Admins can delete deals.")

    title = deal.title
    did = deal.deal_id
    deal.delete()
    log_activity(request.user, 'Deleted', 'Deal', did, title)
    messages.success(request, f"Deal '{title}' ({did}) has been deleted.")
    return redirect('sales:list')


@login_required
def deal_mark_stage(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.user.is_employee_role and deal.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    if request.method == 'POST':
        new_stage = request.POST.get('stage')
        if new_stage in dict(Deal.Stage.choices):
            deal.stage = new_stage
            deal.save()
            log_activity(request.user, f"Marked as {new_stage}", 'Deal', deal.deal_id, deal.title)
            messages.success(request, f"Deal '{deal.title}' marked as {new_stage}.")

    return redirect('sales:detail', pk=pk)


@login_required
def deal_invoice_pdf(request, pk):
    from django.http import HttpResponse
    from .pdf_generator import generate_deal_pdf

    deal = get_object_or_404(Deal, pk=pk)
    if request.user.is_employee_role and deal.assigned_to != request.user:
        raise PermissionDenied("Access restricted.")

    pdf_bytes = generate_deal_pdf(deal)
    prefix = 'Invoice' if deal.stage == 'Won' else 'Quotation'
    filename = f"{prefix}_{deal.deal_id}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

