from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from customers.models import Customer, CustomerNote
from leads.models import Lead
from sales.models import Deal
from tasks.models import Task
from followups.models import FollowUp
from notifications.models import Notification
from activity_logs.models import ActivityLog


class Command(BaseCommand):
    help = 'Seeds realistic enterprise CRM data for SmartCRM demo and testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing SmartCRM database seeding..."))

        # 1. Users / Employees
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartcrm.local',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': User.Role.ADMIN,
                'department': User.Department.MANAGEMENT,
                'phone': '+91 9900011000',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Created Admin: admin / admin123"))

        manager_user, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'anita.deshmukh@smartcrm.local',
                'first_name': 'Anita',
                'last_name': 'Deshmukh',
                'role': User.Role.MANAGER,
                'department': User.Department.MANAGEMENT,
                'phone': '+91 9820012345',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'is_active': True,
            }
        )
        if created:
            manager_user.set_password('pass123')
            manager_user.save()
            self.stdout.write(self.style.SUCCESS(f"Created Manager: manager / pass123"))

        emp1, created = User.objects.get_or_create(
            username='employee',
            defaults={
                'email': 'vikram.malhotra@smartcrm.local',
                'first_name': 'Vikram',
                'last_name': 'Malhotra',
                'role': User.Role.EMPLOYEE,
                'department': User.Department.SALES,
                'phone': '+91 9845012345',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'is_active': True,
            }
        )
        if created:
            emp1.set_password('pass123')
            emp1.save()
            self.stdout.write(self.style.SUCCESS(f"Created Employee: employee / pass123"))

        emp2, created = User.objects.get_or_create(
            username='priya',
            defaults={
                'email': 'priya.nair@smartcrm.local',
                'first_name': 'Priya',
                'last_name': 'Nair',
                'role': User.Role.EMPLOYEE,
                'department': User.Department.SALES,
                'phone': '+91 9940012345',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'is_active': True,
            }
        )
        if created:
            emp2.set_password('pass123')
            emp2.save()

        emp3, created = User.objects.get_or_create(
            username='rohit',
            defaults={
                'email': 'rohit.verma@smartcrm.local',
                'first_name': 'Rohit',
                'last_name': 'Verma',
                'role': User.Role.EMPLOYEE,
                'department': User.Department.SUPPORT,
                'phone': '+91 9711012345',
                'city': 'Delhi',
                'state': 'Delhi NCR',
                'is_active': True,
            }
        )
        if created:
            emp3.set_password('pass123')
            emp3.save()

        all_reps = [emp1, emp2, emp3]

        # 2. Customers
        customer_samples = [
            {
                'full_name': 'Rajesh Singhania',
                'email': 'rajesh@reliancetech.in',
                'phone': '+91 9820198201',
                'company_name': 'Reliance Tech Solutions',
                'address': 'Plot 45, BKC Commercial Complex',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400051',
                'source': Customer.Source.WEBSITE,
                'status': Customer.Status.ACTIVE,
                'assigned_to': emp1,
            },
            {
                'full_name': 'Sunita Murthy',
                'email': 'smurthy@tatadigital.com',
                'phone': '+91 9845198451',
                'company_name': 'Tata Digital Systems',
                'address': 'Level 6, Whitefield Tech Park',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'postal_code': '560066',
                'source': Customer.Source.REFERRAL,
                'status': Customer.Status.ACTIVE,
                'assigned_to': emp2,
            },
            {
                'full_name': 'Arjun Mehra',
                'email': 'arjun@delhifintech.co',
                'phone': '+91 9811198111',
                'company_name': 'Delhi FinTech Corp',
                'address': 'Barakhamba Road, Connaught Place',
                'city': 'Delhi',
                'state': 'Delhi NCR',
                'postal_code': '110001',
                'source': Customer.Source.DIRECT_OUTREACH,
                'status': Customer.Status.ACTIVE,
                'assigned_to': emp1,
            },
            {
                'full_name': 'Kavita Iyer',
                'email': 'kavita@punecloud.io',
                'phone': '+91 9822198221',
                'company_name': 'Pune Cloud Systems',
                'address': 'Hinjewadi Phase 2, IT Corridor',
                'city': 'Pune',
                'state': 'Maharashtra',
                'postal_code': '411057',
                'source': Customer.Source.SOCIAL_MEDIA,
                'status': Customer.Status.ACTIVE,
                'assigned_to': emp2,
            },
            {
                'full_name': 'Naveen Reddy',
                'email': 'naveen@hyderabadbiotech.org',
                'phone': '+91 9849198491',
                'company_name': 'Hyderabad Biotech Ltd',
                'address': 'HITEC City, Madhapur',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'postal_code': '500081',
                'source': Customer.Source.ADVERTISEMENT,
                'status': Customer.Status.ACTIVE,
                'assigned_to': emp3,
            },
            {
                'full_name': 'Amitabh Roy',
                'email': 'aroy@kolkataservices.biz',
                'phone': '+91 9830198301',
                'company_name': 'Kolkata Enterprise Services',
                'address': 'Salt Lake Sector V',
                'city': 'Kolkata',
                'state': 'West Bengal',
                'postal_code': '700091',
                'source': Customer.Source.OTHER,
                'status': Customer.Status.INACTIVE,
                'assigned_to': emp1,
            },
        ]

        created_customers = []
        for cdata in customer_samples:
            cust, _ = Customer.objects.get_or_create(
                email=cdata['email'],
                defaults=cdata
            )
            created_customers.append(cust)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_customers)} customers."))

        # 3. Customer Notes
        if created_customers:
            CustomerNote.objects.get_or_create(
                customer=created_customers[0],
                author=emp1,
                defaults={'content': 'Quarterly executive review meeting went great. Client requested an expansion quote for 50 additional team licenses.'}
            )
            CustomerNote.objects.get_or_create(
                customer=created_customers[1],
                author=emp2,
                defaults={'content': 'Onboarding milestone 1 completed smoothly. System integration with ERP scheduled for next Monday.'}
            )

        # 4. Leads
        lead_samples = [
            {
                'full_name': 'Deepak Khosla',
                'email': 'dkhosla@zenithretail.in',
                'phone': '+91 9810234567',
                'company': 'Zenith Omnichannel Retail',
                'source': Lead.Source.WEBSITE,
                'interested_product': 'CRM Enterprise Suite + API Connector',
                'estimated_deal_value': Decimal('350000.00'),
                'status': Lead.Status.INTERESTED,
                'priority': Lead.Priority.HIGH,
                'assigned_to': emp1,
                'next_followup_date': timezone.now().date() + timedelta(days=2),
                'notes': 'Looking to migrate 120 store reps from spreadsheets to centralized CRM.',
            },
            {
                'full_name': 'Pooja Bhatt',
                'email': 'pooja@nexustech.co',
                'phone': '+91 9820987654',
                'company': 'Nexus Logistics Pvt Ltd',
                'source': Lead.Source.REFERRAL,
                'interested_product': 'SmartCRM Sales & Pipeline Module',
                'estimated_deal_value': Decimal('220000.00'),
                'status': Lead.Status.QUALIFIED,
                'priority': Lead.Priority.HIGH,
                'assigned_to': emp2,
                'next_followup_date': timezone.now().date() + timedelta(days=1),
                'notes': 'Budget approved for Q4. Needs contract agreement and security questionnaire.',
            },
            {
                'full_name': 'Manoj Bajpayee',
                'email': 'manoj@bharatpharma.com',
                'phone': '+91 9845345678',
                'company': 'Bharat Pharma Distro',
                'source': Lead.Source.INSTAGRAM,
                'interested_product': 'Medical Rep Task & Followup Tracking',
                'estimated_deal_value': Decimal('180000.00'),
                'status': Lead.Status.CONTACTED,
                'priority': Lead.Priority.MEDIUM,
                'assigned_to': emp1,
                'next_followup_date': timezone.now().date() + timedelta(days=4),
                'notes': 'Initial phone conversation completed. Demo deck dispatched.',
            },
            {
                'full_name': 'Ritu Varma',
                'email': 'ritu@edutrack.org',
                'phone': '+91 9811456789',
                'company': 'EduTrack Learning Academy',
                'source': Lead.Source.WEBSITE,
                'interested_product': 'Student Admissions CRM',
                'estimated_deal_value': Decimal('95000.00'),
                'status': Lead.Status.NEW,
                'priority': Lead.Priority.MEDIUM,
                'assigned_to': emp3,
                'next_followup_date': timezone.now().date() + timedelta(days=3),
                'notes': 'Inbound contact form submitted via website.',
            },
            {
                'full_name': 'Siddharth Rao',
                'email': 'siddharth@globalinfra.biz',
                'phone': '+91 9900567890',
                'company': 'Global Infra EPC',
                'source': Lead.Source.OTHER,
                'interested_product': 'Enterprise Custom ERP Sync',
                'estimated_deal_value': Decimal('480000.00'),
                'status': Lead.Status.LOST,
                'priority': Lead.Priority.LOW,
                'assigned_to': emp2,
                'lost_reason': 'Selected offshore bespoke software vendor with fixed legacy software integration.',
            },
            {
                'full_name': 'Gaurav Sen',
                'email': 'gaurav@cloudscale.net',
                'phone': '+91 9711678901',
                'company': 'CloudScale Microservices',
                'source': Lead.Source.REFERRAL,
                'interested_product': 'SmartCRM Core Suite',
                'estimated_deal_value': Decimal('160000.00'),
                'status': Lead.Status.CONVERTED,
                'priority': Lead.Priority.HIGH,
                'assigned_to': emp1,
                'converted_customer': created_customers[0] if created_customers else None,
            },
        ]

        created_leads = []
        for ldata in lead_samples:
            ld, _ = Lead.objects.get_or_create(
                email=ldata['email'],
                defaults=ldata
            )
            created_leads.append(ld)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_leads)} leads."))

        # 5. Sales Deals
        today = timezone.now().date()
        deal_samples = [
            {
                'title': 'Reliance Tech Annual CRM Deployment',
                'customer': created_customers[0],
                'assigned_to': emp1,
                'deal_value': Decimal('450000.00'),
                'stage': Deal.Stage.WON,
                'expected_closing_date': today - timedelta(days=15),
                'actual_closing_date': today - timedelta(days=15),
                'notes': 'Closed annual subscription with 75 user seats.',
            },
            {
                'title': 'Tata Digital Cloud Integration Contract',
                'customer': created_customers[1],
                'assigned_to': emp2,
                'deal_value': Decimal('680000.00'),
                'stage': Deal.Stage.WON,
                'expected_closing_date': today - timedelta(days=45),
                'actual_closing_date': today - timedelta(days=45),
                'notes': 'Multi-location enterprise rollout package.',
            },
            {
                'title': 'Delhi FinTech Core CRM License',
                'customer': created_customers[2],
                'assigned_to': emp1,
                'deal_value': Decimal('320000.00'),
                'stage': Deal.Stage.NEGOTIATION,
                'expected_closing_date': today + timedelta(days=12),
                'notes': 'Final commercial negotiation with CFO.',
            },
            {
                'title': 'Pune Cloud Systems Tier-2 Support Addon',
                'customer': created_customers[3],
                'assigned_to': emp2,
                'deal_value': Decimal('145000.00'),
                'stage': Deal.Stage.PROPOSAL,
                'expected_closing_date': today + timedelta(days=20),
                'notes': 'Proposal delivered to technology director.',
            },
            {
                'title': 'Hyderabad Biotech SaaS Standard Package',
                'customer': created_customers[4],
                'assigned_to': emp3,
                'deal_value': Decimal('210000.00'),
                'stage': Deal.Stage.NEW,
                'expected_closing_date': today + timedelta(days=35),
                'notes': 'Initial requirements questionnaire submitted.',
            },
            {
                'title': 'Kolkata Legacy Migration Project',
                'customer': created_customers[5],
                'assigned_to': emp1,
                'deal_value': Decimal('120000.00'),
                'stage': Deal.Stage.LOST,
                'expected_closing_date': today - timedelta(days=25),
                'actual_closing_date': today - timedelta(days=20),
                'notes': 'Client deferred CRM budget until next fiscal year.',
            },
        ]

        for ddata in deal_samples:
            Deal.objects.get_or_create(
                title=ddata['title'],
                defaults=ddata
            )
        self.stdout.write(self.style.SUCCESS("Seeded sales deals with verified Won revenue."))

        # 6. Tasks
        task_samples = [
            {
                'title': 'Deliver customized security questionnaire to Tata Digital',
                'description': 'Complete Section 4 (Data Encryption & Cloud Storage Compliance) and email by EOD.',
                'assigned_to': emp2,
                'created_by': manager_user,
                'customer': created_customers[1],
                'priority': Task.Priority.URGENT,
                'status': Task.Status.IN_PROGRESS,
                'due_date': today + timedelta(days=1),
            },
            {
                'title': 'Finalize contract draft for Delhi FinTech Corp',
                'description': 'Ensure net-30 payment term and SLA schedule A are included.',
                'assigned_to': emp1,
                'created_by': manager_user,
                'customer': created_customers[2],
                'priority': Task.Priority.HIGH,
                'status': Task.Status.PENDING,
                'due_date': today + timedelta(days=3),
            },
            {
                'title': 'Product demonstration with Zenith Retail IT Leadership',
                'description': 'Demonstrate role-based views and mobile responsiveness.',
                'assigned_to': emp1,
                'created_by': emp1,
                'lead': created_leads[0] if created_leads else None,
                'priority': Task.Priority.HIGH,
                'status': Task.Status.PENDING,
                'due_date': today + timedelta(days=2),
            },
            {
                'title': 'Resolve data import query for Reliance Tech',
                'description': 'Review CSV format of legacy lead database and assist with bulk mapping.',
                'assigned_to': emp3,
                'created_by': admin_user,
                'customer': created_customers[0],
                'priority': Task.Priority.MEDIUM,
                'status': Task.Status.COMPLETED,
                'due_date': today - timedelta(days=3),
                'completed_at': timezone.now() - timedelta(days=3),
            },
            {
                'title': 'Submit weekly pipeline forecast report to management',
                'description': 'Consolidate weighted deals closing this calendar month.',
                'assigned_to': emp1,
                'created_by': manager_user,
                'priority': Task.Priority.URGENT,
                'status': Task.Status.PENDING,
                'due_date': today - timedelta(days=2),  # intentionally overdue
            },
        ]

        for tdata in task_samples:
            Task.objects.get_or_create(
                title=tdata['title'],
                defaults=tdata
            )
        self.stdout.write(self.style.SUCCESS("Seeded tasks including pending, completed, and overdue states."))

        # 7. Follow-ups (spread across current month calendar)
        followup_samples = [
            {
                'customer': created_customers[0],
                'assigned_to': emp1,
                'followup_date': today,
                'followup_time': '11:00:00',
                'followup_type': FollowUp.Type.CALL,
                'description': 'Discussion on annual renewal terms and expansion user count.',
                'status': FollowUp.Status.PENDING,
            },
            {
                'customer': created_customers[1],
                'assigned_to': emp2,
                'followup_date': today + timedelta(days=1),
                'followup_time': '15:30:00',
                'followup_type': FollowUp.Type.MEETING,
                'description': 'Executive sprint alignment with Tata Digital VP.',
                'status': FollowUp.Status.PENDING,
            },
            {
                'customer': created_customers[2],
                'assigned_to': emp1,
                'followup_date': today + timedelta(days=4),
                'followup_time': '14:00:00',
                'followup_type': FollowUp.Type.CALL,
                'description': 'Commercial agreement sign-off verification.',
                'status': FollowUp.Status.PENDING,
            },
            {
                'lead': created_leads[0] if created_leads else None,
                'assigned_to': emp1,
                'followup_date': today + timedelta(days=2),
                'followup_time': '10:00:00',
                'followup_type': FollowUp.Type.MEETING,
                'description': 'Live product walkthrough with retail territory leads.',
                'status': FollowUp.Status.PENDING,
            },
            {
                'customer': created_customers[3],
                'assigned_to': emp2,
                'followup_date': today - timedelta(days=5),
                'followup_time': '16:00:00',
                'followup_type': FollowUp.Type.EMAIL,
                'description': 'Sent proposal quotation document and SLA guidelines.',
                'status': FollowUp.Status.COMPLETED,
                'outcome': 'Client confirmed receipt and schedule review for next Friday.',
            },
            {
                'customer': created_customers[4],
                'assigned_to': emp3,
                'followup_date': today - timedelta(days=2),
                'followup_time': '11:30:00',
                'followup_type': FollowUp.Type.CALL,
                'description': 'Clarification on support tickets and response guarantees.',
                'status': FollowUp.Status.PENDING,  # Overdue
            },
        ]

        for fdata in followup_samples:
            FollowUp.objects.get_or_create(
                description=fdata['description'],
                defaults=fdata
            )
        self.stdout.write(self.style.SUCCESS("Seeded calendar follow-ups."))

        # 8. Notifications
        Notification.objects.get_or_create(
            recipient=admin_user,
            title="System Initialization Complete",
            defaults={
                'message': 'SmartCRM Enterprise environment is operational with all 11 modules initialized.',
                'notification_type': Notification.NotificationType.SYSTEM,
                'is_read': False,
                'link': '/dashboard/'
            }
        )
        Notification.objects.get_or_create(
            recipient=emp1,
            title="High Value Deal in Negotiation",
            defaults={
                'message': "Deal 'Delhi FinTech Core CRM License' (₹3,20,000) target close date is approaching.",
                'notification_type': Notification.NotificationType.DEAL,
                'is_read': False,
                'link': '/sales/'
            }
        )
        Notification.objects.get_or_create(
            recipient=emp2,
            title="Urgent Task Due Soon",
            defaults={
                'message': "Task 'Deliver customized security questionnaire to Tata Digital' is due tomorrow.",
                'notification_type': Notification.NotificationType.TASK,
                'is_read': False,
                'link': '/tasks/'
            }
        )

        # 9. Activity Logs
        ActivityLog.objects.get_or_create(
            action="System Initialized",
            model_name="System",
            defaults={
                'user': admin_user,
                'object_id': "SYS-001",
                'object_repr': "SmartCRM Enterprise Suite",
                'details': "All modular applications, database constraints, and demo datasets populated."
            }
        )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
