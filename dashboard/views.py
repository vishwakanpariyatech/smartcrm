import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from customers.models import Customer
from leads.models import Lead
from sales.models import Deal
from tasks.models import Task
from followups.models import FollowUp
from accounts.models import User
from activity_logs.models import ActivityLog


@login_required
def dashboard_index(request):
    user = request.user
    today = timezone.now().date()

    # Role-based querysets
    if user.is_superuser or user.is_admin_role or user.is_manager_role:
        customers_qs = Customer.objects.all()
        leads_qs = Lead.objects.all()
        deals_qs = Deal.objects.all()
        tasks_qs = Task.objects.all()
        followups_qs = FollowUp.objects.all()
        activities_qs = ActivityLog.objects.all()
    else:
        customers_qs = Customer.objects.filter(assigned_to=user)
        leads_qs = Lead.objects.filter(assigned_to=user)
        deals_qs = Deal.objects.filter(assigned_to=user)
        tasks_qs = Task.objects.filter(Q(assigned_to=user) | Q(created_by=user))
        followups_qs = FollowUp.objects.filter(assigned_to=user)
        activities_qs = ActivityLog.objects.filter(user=user)

    # 1. Metric Card Statistics
    total_customers = customers_qs.count()
    total_leads = leads_qs.count()
    converted_leads = leads_qs.filter(status='Converted').count()
    won_deals = deals_qs.filter(stage='Won')
    total_sales_revenue = won_deals.aggregate(v=Sum('deal_value'))['v'] or 0
    pending_tasks = tasks_qs.filter(status__in=['Pending', 'In Progress']).count()
    overdue_tasks = tasks_qs.filter(due_date__lt=today).exclude(status='Completed').count()
    active_employees = User.objects.filter(is_active=True).count()
    upcoming_followups = followups_qs.filter(followup_date__gte=today, status='Pending').count()

    # 2. Monthly Sales Bar Chart (Last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_sales = (
        deals_qs.filter(stage='Won', created_at__date__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('deal_value'))
        .order_by('month')
    )

    sales_months_labels = []
    sales_months_data = []
    for item in monthly_sales:
        if item['month']:
            sales_months_labels.append(item['month'].strftime('%b %Y'))
            sales_months_data.append(float(item['total'] or 0))

    if not sales_months_labels:
        # Default placeholder for chart if no past data
        sales_months_labels = [(today - timedelta(days=30*i)).strftime('%b %Y') for i in reversed(range(6))]
        sales_months_data = [0, 0, 0, 0, 0, float(total_sales_revenue)]

    # 3. Lead Conversion Doughnut Chart
    lead_status_counts = leads_qs.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in lead_status_counts}
    lead_chart_labels = ['New', 'Contacted', 'Interested', 'Qualified', 'Converted', 'Lost']
    lead_chart_data = [status_dict.get(s, 0) for s in lead_chart_labels]

    # 4. Customer Growth Line Chart
    customer_growth = (
        customers_qs.filter(created_at__date__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    growth_labels = []
    growth_data = []
    for cg in customer_growth:
        if cg['month']:
            growth_labels.append(cg['month'].strftime('%b %Y'))
            growth_data.append(cg['count'])

    if not growth_labels:
        growth_labels = sales_months_labels
        growth_data = [0, 0, 0, 0, 0, total_customers]

    # 5. Tables & Feeds
    recent_customers = customers_qs.order_by('-created_at')[:5]
    recent_sales = deals_qs.order_by('-created_at')[:5]
    upcoming_followup_list = followups_qs.filter(followup_date__gte=today, status='Pending').order_by('followup_date', 'followup_time')[:5]
    recent_activities = activities_qs.order_by('-timestamp')[:8] if (request.user.is_superuser or request.user.is_admin_role) else []

    context = {
        'total_customers': total_customers,
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'total_sales_revenue': total_sales_revenue,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'active_employees': active_employees,
        'upcoming_followups': upcoming_followups,
        # JSON data for Chart.js
        'sales_labels_json': json.dumps(sales_months_labels),
        'sales_data_json': json.dumps(sales_months_data),
        'lead_labels_json': json.dumps(lead_chart_labels),
        'lead_data_json': json.dumps(lead_chart_data),
        'growth_labels_json': json.dumps(growth_labels),
        'growth_data_json': json.dumps(growth_data),
        # Recent records
        'recent_customers': recent_customers,
        'recent_sales': recent_sales,
        'upcoming_followup_list': upcoming_followup_list,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def global_search(request):
    """Global search across permitted customer, lead, and deal records."""
    query = request.GET.get('q', '').strip()
    user = request.user

    customers = []
    leads = []
    deals = []

    if query:
        cust_qs = Customer.objects.all() if (user.is_superuser or user.is_admin_role or user.is_manager_role) else Customer.objects.filter(assigned_to=user)
        lead_qs = Lead.objects.all() if (user.is_superuser or user.is_admin_role or user.is_manager_role) else Lead.objects.filter(assigned_to=user)
        deal_qs = Deal.objects.all() if (user.is_superuser or user.is_admin_role or user.is_manager_role) else Deal.objects.filter(assigned_to=user)

        customers = cust_qs.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(company_name__icontains=query) |
            Q(customer_id__icontains=query)
        )[:10]

        leads = lead_qs.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(company__icontains=query) |
            Q(lead_id__icontains=query)
        )[:10]

        deals = deal_qs.filter(
            Q(title__icontains=query) |
            Q(deal_id__icontains=query) |
            Q(customer__full_name__icontains=query)
        )[:10]

    context = {
        'query': query,
        'customers': customers,
        'leads': leads,
        'deals': deals,
        'total_results': len(customers) + len(leads) + len(deals),
    }
    return render(request, 'dashboard/search_results.html', context)


@login_required
def quick_add(request):
    """Universal Quick Add handler for Leads, Tasks, and Customers from navbar."""
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        return_url = request.META.get('HTTP_REFERER', 'dashboard:index')

        if item_type == 'lead':
            name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            company = request.POST.get('company', '').strip()
            source = request.POST.get('source', 'Website')
            deal_val = request.POST.get('deal_value') or '0'
            priority = request.POST.get('priority', 'Medium')

            if name and (email or phone):
                lead = Lead.objects.create(
                    full_name=name,
                    email=email or f"lead_{int(timezone.now().timestamp())}@example.com",
                    phone=phone or "+91 9000000000",
                    company=company,
                    source=source if source in dict(Lead.Source.choices) else Lead.Source.OTHER,
                    estimated_deal_value=float(deal_val) if deal_val else 0,
                    priority=priority if priority in dict(Lead.Priority.choices) else Lead.Priority.MEDIUM,
                    assigned_to=request.user
                )
                log_activity(request.user, 'Quick Added', 'Lead', lead.lead_id, lead.full_name)
                messages.success(request, f"Lead '{lead.full_name}' ({lead.lead_id}) added via Quick Add!")
                return redirect('leads:detail', pk=lead.pk)
            else:
                messages.error(request, "Please enter at least Name and Phone/Email for the lead.")

        elif item_type == 'task':
            title = request.POST.get('title', '').strip()
            priority = request.POST.get('priority', 'Medium')
            due_date = request.POST.get('due_date')

            if title:
                task = Task.objects.create(
                    title=title,
                    priority=priority if priority in dict(Task.Priority.choices) else Task.Priority.MEDIUM,
                    due_date=due_date if due_date else timezone.now().date(),
                    assigned_to=request.user,
                    created_by=request.user
                )
                log_activity(request.user, 'Quick Added', 'Task', task.task_id, task.title)
                messages.success(request, f"Task '{task.title}' ({task.task_id}) created successfully!")
                return redirect('tasks:list')
            else:
                messages.error(request, "Task title is required.")

        elif item_type == 'customer':
            name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            company = request.POST.get('company_name', '').strip()
            city = request.POST.get('city', '').strip()

            if name and email and phone:
                customer = Customer.objects.create(
                    full_name=name,
                    email=email,
                    phone=phone,
                    company_name=company,
                    city=city,
                    assigned_to=request.user
                )
                log_activity(request.user, 'Quick Added', 'Customer', customer.customer_id, customer.full_name)
                messages.success(request, f"Customer '{customer.full_name}' ({customer.customer_id}) added successfully!")
                return redirect('customers:detail', pk=customer.pk)
            else:
                messages.error(request, "Customer Full Name, Email, and Phone are required.")

        return redirect(return_url)

    return redirect('dashboard:index')

