from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from .models import Lead
from .forms import LeadForm, ConvertLeadForm
from customers.models import Customer
from sales.models import Deal
from accounts.models import User
from activity_logs.models import log_activity, ActivityLog
from notifications.models import create_notification


def get_user_leads_qs(user):
    """Scoped Lead queryset based on user role."""
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        return Lead.objects.all()
    return Lead.objects.filter(assigned_to=user)


@login_required
def lead_list(request):
    leads = get_user_leads_qs(request.user)

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    priority_filter = request.GET.get('priority', '')
    employee_filter = request.GET.get('employee', '')

    if query:
        leads = leads.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(company__icontains=query) |
            Q(lead_id__icontains=query) |
            Q(interested_product__icontains=query)
        )

    if status_filter:
        leads = leads.filter(status=status_filter)

    if source_filter:
        leads = leads.filter(source=source_filter)

    if priority_filter:
        leads = leads.filter(priority=priority_filter)

    if employee_filter and (request.user.is_admin_role or request.user.is_manager_role):
        leads = leads.filter(assigned_to_id=employee_filter)

    # Conversion summary stats
    total_count = leads.count()
    converted_count = leads.filter(status='Converted').count()
    conversion_rate = round((converted_count / total_count * 100), 1) if total_count > 0 else 0
    pipeline_value = leads.exclude(status__in=['Converted', 'Lost']).aggregate(val=Sum('estimated_deal_value'))['val'] or 0

    paginator = Paginator(leads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    employees = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'priority_filter': priority_filter,
        'employee_filter': employee_filter,
        'statuses': Lead.Status.choices,
        'sources': Lead.Source.choices,
        'priorities': Lead.Priority.choices,
        'employees': employees,
        'total_count': total_count,
        'converted_count': converted_count,
        'conversion_rate': conversion_rate,
        'pipeline_value': pipeline_value,
    }
    return render(request, 'leads/lead_list.html', context)


@login_required
def lead_pipeline(request):
    """Kanban-style Pipeline View grouped by lead stage."""
    leads = get_user_leads_qs(request.user)

    stages = ['New', 'Contacted', 'Interested', 'Qualified', 'Converted', 'Lost']
    pipeline_data = {}
    for stage in stages:
        stage_leads = leads.filter(status=stage)
        stage_val = stage_leads.aggregate(v=Sum('estimated_deal_value'))['v'] or 0
        pipeline_data[stage] = {
            'leads': stage_leads,
            'count': stage_leads.count(),
            'total_value': stage_val,
        }

    context = {
        'pipeline_data': pipeline_data,
        'stages': stages,
    }
    return render(request, 'leads/lead_pipeline.html', context)


@login_required
def lead_create(request):
    if request.method == 'POST':
        form = LeadForm(request.POST, user=request.user)
        if form.is_valid():
            lead = form.save(commit=False)
            if request.user.is_employee_role and not lead.assigned_to:
                lead.assigned_to = request.user
            lead.save()

            log_activity(request.user, 'Created', 'Lead', lead.lead_id, lead.full_name)
            if lead.assigned_to and lead.assigned_to != request.user:
                create_notification(
                    lead.assigned_to,
                    'New Lead Assigned',
                    f"Lead {lead.full_name} ({lead.company}) assigned to you.",
                    'lead',
                    f"/leads/{lead.pk}/"
                )
            messages.success(request, f"Lead {lead.full_name} ({lead.lead_id}) created successfully.")
            return redirect('leads:detail', pk=lead.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = LeadForm(user=request.user)

    return render(request, 'leads/lead_form.html', {'form': form, 'title': 'Add New Lead'})


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if request.user.is_employee_role and lead.assigned_to != request.user:
        raise PermissionDenied("Access to this lead record is restricted.")

    followups = lead.followups.all().order_by('-followup_date')
    convert_form = ConvertLeadForm(initial={
        'deal_title': f"Project: {lead.interested_product or lead.company or lead.full_name}",
        'deal_value': lead.estimated_deal_value,
        'expected_closing_date': timezone.now().date() + timezone.timedelta(days=30),
    })

    recent_activities = ActivityLog.objects.filter(
        model_name='Lead', object_id=lead.lead_id
    ).order_by('-timestamp')[:10]

    context = {
        'lead': lead,
        'followups': followups,
        'convert_form': convert_form,
        'recent_activities': recent_activities,
    }
    return render(request, 'leads/lead_detail.html', context)


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if request.user.is_employee_role and lead.assigned_to != request.user:
        raise PermissionDenied("Access to modify this lead record is restricted.")

    old_status = lead.status
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead, user=request.user)
        if form.is_valid():
            updated_lead = form.save()
            if updated_lead.status != old_status:
                log_activity(request.user, f"Status changed: {old_status} -> {updated_lead.status}", 'Lead', lead.lead_id, lead.full_name)
            else:
                log_activity(request.user, 'Updated', 'Lead', lead.lead_id, lead.full_name)
            messages.success(request, f"Lead {lead.full_name} updated successfully.")
            return redirect('leads:detail', pk=lead.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = LeadForm(instance=lead, user=request.user)

    return render(request, 'leads/lead_form.html', {
        'form': form,
        'title': f'Edit Lead: {lead.full_name}',
        'lead': lead
    })


@login_required
def lead_delete(request, pk):
    if request.method != 'POST':
        return redirect('leads:list')

    lead = get_object_or_404(Lead, pk=pk)
    if not (request.user.is_admin_role or request.user.is_manager_role):
        raise PermissionDenied("Only Managers and Admins can delete lead records.")

    name = lead.full_name
    lid = lead.lead_id
    lead.delete()
    log_activity(request.user, 'Deleted', 'Lead', lid, name)
    messages.success(request, f"Lead {name} ({lid}) has been deleted.")
    return redirect('leads:list')


@login_required
def lead_convert(request, pk):
    """
    Convert a qualified lead into a customer:
    - Creates or retrieves customer
    - Links lead to customer
    - Marks lead status as Converted
    - Optionally creates a Sales Deal
    - Keeps full history
    """
    lead = get_object_or_404(Lead, pk=pk)

    if request.user.is_employee_role and lead.assigned_to != request.user:
        raise PermissionDenied("Permission denied.")

    if request.method == 'POST':
        form = ConvertLeadForm(request.POST)
        if form.is_valid():
            # 1. Create or match customer
            customer = Customer.objects.filter(email=lead.email).first()
            if not customer:
                customer = Customer.objects.create(
                    full_name=lead.full_name,
                    email=lead.email,
                    phone=lead.phone,
                    company_name=lead.company,
                    source=lead.source if lead.source in dict(Customer.Source.choices) else Customer.Source.OTHER,
                    status=Customer.Status.ACTIVE,
                    assigned_to=lead.assigned_to,
                    notes=f"Converted from Lead {lead.lead_id}.\n{lead.notes}"
                )
                log_activity(request.user, 'Created via Conversion', 'Customer', customer.customer_id, customer.full_name)

            # 2. Update Lead
            lead.status = Lead.Status.CONVERTED
            lead.converted_customer = customer
            lead.save()
            log_activity(request.user, 'Converted to Customer', 'Lead', lead.lead_id, lead.full_name, f"Customer: {customer.customer_id}")

            # 3. Create initial Deal if chosen
            if form.cleaned_data.get('create_deal'):
                deal_title = form.cleaned_data.get('deal_title') or f"Deal with {customer.full_name}"
                deal_val = form.cleaned_data.get('deal_value') or lead.estimated_deal_value
                closing_date = form.cleaned_data.get('expected_closing_date') or (timezone.now().date() + timezone.timedelta(days=30))
                deal = Deal.objects.create(
                    title=deal_title,
                    customer=customer,
                    lead=lead,
                    assigned_to=lead.assigned_to or request.user,
                    deal_value=deal_val,
                    stage=Deal.Stage.PROPOSAL,
                    expected_closing_date=closing_date,
                    notes=f"Generated upon lead conversion: {lead.lead_id}"
                )
                log_activity(request.user, 'Created from Lead', 'Deal', deal.deal_id, deal.title)

            messages.success(request, f"Lead successfully converted to Customer {customer.full_name} ({customer.customer_id})!")
            return redirect('customers:detail', pk=customer.pk)
        else:
            messages.error(request, "Conversion details were invalid.")

    return redirect('leads:detail', pk=pk)


@login_required
def lead_update_stage(request, pk):
    """Update lead status from pipeline board via quick action or Drag-and-Drop AJAX."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    if request.method == 'POST':
        lead = get_object_or_404(Lead, pk=pk)
        if request.user.is_employee_role and lead.assigned_to != request.user:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'You can only update leads assigned to you.'}, status=403)
            raise PermissionDenied("Access restricted.")

        new_status = request.POST.get('status')
        if new_status in dict(Lead.Status.choices):
            old_status = lead.status
            lead.status = new_status
            if new_status == 'Lost':
                lead.lost_reason = request.POST.get('lost_reason', 'Not specified')
            lead.save()
            log_activity(request.user, f"Status changed to {new_status}", 'Lead', lead.lead_id, lead.full_name)

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': f"Lead {lead.full_name} moved from {old_status} to {new_status}.",
                    'lead_id': lead.id,
                    'new_status': new_status,
                    'old_status': old_status
                })

            messages.success(request, f"Lead {lead.full_name} moved from {old_status} to {new_status}.")

    if is_ajax:
        return JsonResponse({'status': 'error', 'message': 'Invalid request or status.'}, status=400)
    return redirect(request.META.get('HTTP_REFERER', 'leads:pipeline'))
