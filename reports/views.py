import csv
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from customers.models import Customer
from leads.models import Lead
from sales.models import Deal
from tasks.models import Task
from followups.models import FollowUp
from accounts.models import User
from accounts.permissions import role_required


@login_required
def reports_index(request):
    user = request.user
    today = timezone.now().date()

    # Filters
    report_type = request.GET.get('type', 'sales')  # sales, leads, customers, employees, tasks, followups
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    employee_id = request.GET.get('employee', '')

    # Base querysets respecting user permissions
    is_admin_or_mgr = user.is_superuser or user.is_admin_role or user.is_manager_role

    deals_qs = Deal.objects.all() if is_admin_or_mgr else Deal.objects.filter(assigned_to=user)
    leads_qs = Lead.objects.all() if is_admin_or_mgr else Lead.objects.filter(assigned_to=user)
    customers_qs = Customer.objects.all() if is_admin_or_mgr else Customer.objects.filter(assigned_to=user)
    tasks_qs = Task.objects.all() if is_admin_or_mgr else Task.objects.filter(assigned_to=user)
    followups_qs = FollowUp.objects.all() if is_admin_or_mgr else FollowUp.objects.filter(assigned_to=user)

    if from_date:
        deals_qs = deals_qs.filter(created_at__date__gte=from_date)
        leads_qs = leads_qs.filter(created_at__date__gte=from_date)
        customers_qs = customers_qs.filter(created_at__date__gte=from_date)
        tasks_qs = tasks_qs.filter(created_at__date__gte=from_date)
        followups_qs = followups_qs.filter(followup_date__gte=from_date)

    if to_date:
        deals_qs = deals_qs.filter(created_at__date__lte=to_date)
        leads_qs = leads_qs.filter(created_at__date__lte=to_date)
        customers_qs = customers_qs.filter(created_at__date__lte=to_date)
        tasks_qs = tasks_qs.filter(created_at__date__lte=to_date)
        followups_qs = followups_qs.filter(followup_date__lte=to_date)

    if employee_id and is_admin_or_mgr:
        deals_qs = deals_qs.filter(assigned_to_id=employee_id)
        leads_qs = leads_qs.filter(assigned_to_id=employee_id)
        customers_qs = customers_qs.filter(assigned_to_id=employee_id)
        tasks_qs = tasks_qs.filter(assigned_to_id=employee_id)
        followups_qs = followups_qs.filter(assigned_to_id=employee_id)

    # Calculate summaries based on report_type
    summary_data = {}
    chart_labels = []
    chart_values = []
    table_rows = []

    if report_type == 'sales':
        won_deals = deals_qs.filter(stage='Won')
        total_won = won_deals.aggregate(v=Sum('deal_value'))['v'] or 0
        total_pipeline = deals_qs.exclude(stage__in=['Won', 'Lost']).aggregate(v=Sum('deal_value'))['v'] or 0
        total_count = deals_qs.count()
        won_count = won_deals.count()

        summary_data = {
            'card1_label': 'Total Revenue (Won)', 'card1_val': f"₹{total_won:,.2f}",
            'card2_label': 'Active Pipeline Value', 'card2_val': f"₹{total_pipeline:,.2f}",
            'card3_label': 'Total Deals Logged', 'card3_val': total_count,
            'card4_label': 'Won Deals Count', 'card4_val': won_count,
        }

        # Stage breakdown for chart
        stages = Deal.Stage.choices
        for s_val, s_label in stages:
            chart_labels.append(s_label)
            val = deals_qs.filter(stage=s_val).aggregate(v=Sum('deal_value'))['v'] or 0
            chart_values.append(float(val))

        table_rows = deals_qs.order_by('-created_at')[:50]

    elif report_type == 'leads':
        total_leads = leads_qs.count()
        converted = leads_qs.filter(status='Converted').count()
        lost = leads_qs.filter(status='Lost').count()
        conv_rate = round((converted / total_leads * 100), 1) if total_leads > 0 else 0

        summary_data = {
            'card1_label': 'Total Leads Captured', 'card1_val': total_leads,
            'card2_label': 'Converted to Customers', 'card2_val': converted,
            'card3_label': 'Conversion Rate', 'card3_val': f"{conv_rate}%",
            'card4_label': 'Lost Leads', 'card4_val': lost,
        }

        # Source breakdown for chart
        sources = Lead.Source.choices
        for src_val, src_label in sources:
            chart_labels.append(src_label)
            chart_values.append(leads_qs.filter(source=src_val).count())

        table_rows = leads_qs.order_by('-created_at')[:50]

    elif report_type == 'customers':
        total_cust = customers_qs.count()
        active_cust = customers_qs.filter(status='Active').count()
        inactive_cust = customers_qs.filter(status='Inactive').count()
        top_city = customers_qs.values('city').annotate(c=Count('id')).order_by('-c').first()

        summary_data = {
            'card1_label': 'Total Accounts', 'card1_val': total_cust,
            'card2_label': 'Active Accounts', 'card2_val': active_cust,
            'card3_label': 'Inactive Accounts', 'card3_val': inactive_cust,
            'card4_label': 'Top Region', 'card4_val': top_city['city'] if top_city and top_city['city'] else 'N/A',
        }

        # City breakdown
        cities = customers_qs.values('city').annotate(c=Count('id')).order_by('-c')[:6]
        for c in cities:
            chart_labels.append(c['city'] or 'Unspecified')
            chart_values.append(c['c'])

        table_rows = customers_qs.order_by('-created_at')[:50]

    elif report_type == 'employees':
        active_emp = User.objects.filter(is_active=True).count()
        total_sales_all = Deal.objects.filter(stage='Won').aggregate(v=Sum('deal_value'))['v'] or 0

        summary_data = {
            'card1_label': 'Active Team Members', 'card1_val': active_emp,
            'card2_label': 'Won Sales Across Team', 'card2_val': f"₹{total_sales_all:,.0f}",
            'card3_label': 'Total Assigned Customers', 'card3_val': Customer.objects.filter(assigned_to__isnull=False).count(),
            'card4_label': 'Total Assigned Leads', 'card4_val': Lead.objects.filter(assigned_to__isnull=False).count(),
        }

        # Sales won per employee
        emp_list = User.objects.filter(is_active=True)
        for emp in emp_list[:8]:
            chart_labels.append(emp.display_name)
            emp_won = Deal.objects.filter(assigned_to=emp, stage='Won').aggregate(v=Sum('deal_value'))['v'] or 0
            chart_values.append(float(emp_won))

        table_rows = emp_list

    elif report_type == 'tasks':
        total_t = tasks_qs.count()
        comp_t = tasks_qs.filter(status='Completed').count()
        overdue_t = tasks_qs.filter(due_date__lt=today).exclude(status='Completed').count()
        comp_rate = round((comp_t / total_t * 100), 1) if total_t > 0 else 0

        summary_data = {
            'card1_label': 'Total Tasks', 'card1_val': total_t,
            'card2_label': 'Completed Tasks', 'card2_val': comp_t,
            'card3_label': 'Completion Rate', 'card3_val': f"{comp_rate}%",
            'card4_label': 'Overdue Tasks', 'card4_val': overdue_t,
        }

        for st in ['Pending', 'In Progress', 'Completed']:
            chart_labels.append(st)
            chart_values.append(tasks_qs.filter(status=st).count())

        table_rows = tasks_qs.order_by('-due_date')[:50]

    employees = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'report_type': report_type,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id': employee_id,
        'employees': employees,
        'summary_data': summary_data,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'table_rows': table_rows,
        'now': timezone.now(),
    }
    return render(request, 'reports/reports_index.html', context)


@login_required
def export_csv_report(request):
    """Generate dynamic CSV export based on active report type and filters."""
    user = request.user
    report_type = request.GET.get('type', 'sales')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    employee_id = request.GET.get('employee', '')

    is_admin_or_mgr = user.is_superuser or user.is_admin_role or user.is_manager_role

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="smartcrm_{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    if report_type == 'sales':
        deals = Deal.objects.all() if is_admin_or_mgr else Deal.objects.filter(assigned_to=user)
        if from_date: deals = deals.filter(created_at__date__gte=from_date)
        if to_date: deals = deals.filter(created_at__date__lte=to_date)
        if employee_id and is_admin_or_mgr: deals = deals.filter(assigned_to_id=employee_id)

        writer.writerow(['Deal ID', 'Title', 'Customer', 'Value (INR)', 'Stage', 'Expected Closing', 'Actual Closing', 'Assigned Rep', 'Created Date'])
        for d in deals:
            writer.writerow([
                d.deal_id, d.title, d.customer.full_name, d.deal_value,
                d.stage, d.expected_closing_date, d.actual_closing_date or '',
                d.assigned_to.display_name, d.created_at.strftime('%Y-%m-%d')
            ])

    elif report_type == 'leads':
        leads = Lead.objects.all() if is_admin_or_mgr else Lead.objects.filter(assigned_to=user)
        if from_date: leads = leads.filter(created_at__date__gte=from_date)
        if to_date: leads = leads.filter(created_at__date__lte=to_date)
        if employee_id and is_admin_or_mgr: leads = leads.filter(assigned_to_id=employee_id)

        writer.writerow(['Lead ID', 'Full Name', 'Company', 'Email', 'Phone', 'Source', 'Est. Value', 'Status', 'Priority', 'Assigned Rep', 'Created Date'])
        for l in leads:
            writer.writerow([
                l.lead_id, l.full_name, l.company, l.email, l.phone,
                l.source, l.estimated_deal_value, l.status, l.priority,
                l.assigned_to.display_name if l.assigned_to else 'Unassigned',
                l.created_at.strftime('%Y-%m-%d')
            ])

    elif report_type == 'customers':
        customers = Customer.objects.all() if is_admin_or_mgr else Customer.objects.filter(assigned_to=user)
        if from_date: customers = customers.filter(created_at__date__gte=from_date)
        if to_date: customers = customers.filter(created_at__date__lte=to_date)
        if employee_id and is_admin_or_mgr: customers = customers.filter(assigned_to_id=employee_id)

        writer.writerow(['Customer ID', 'Full Name', 'Company', 'Email', 'Phone', 'City', 'Status', 'Assigned Rep', 'Created Date'])
        for c in customers:
            writer.writerow([
                c.customer_id, c.full_name, c.company_name, c.email, c.phone,
                c.city, c.status, c.assigned_to.display_name if c.assigned_to else 'Unassigned',
                c.created_at.strftime('%Y-%m-%d')
            ])

    elif report_type == 'tasks':
        tasks = Task.objects.all() if is_admin_or_mgr else Task.objects.filter(assigned_to=user)
        if from_date: tasks = tasks.filter(created_at__date__gte=from_date)
        if to_date: tasks = tasks.filter(created_at__date__lte=to_date)
        if employee_id and is_admin_or_mgr: tasks = tasks.filter(assigned_to_id=employee_id)

        writer.writerow(['Task ID', 'Title', 'Assigned To', 'Priority', 'Status', 'Due Date', 'Completed At'])
        for t in tasks:
            writer.writerow([
                t.task_id, t.title, t.assigned_to.display_name, t.priority,
                t.status, t.due_date, t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else ''
            ])

    return response
