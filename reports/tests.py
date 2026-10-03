from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer
from sales.models import Deal


class ReportsAndAnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_reports',
            email='admin_rep@crm.test',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.customer = Customer.objects.create(
            full_name='Report Client',
            email='rep_client@test.com',
            phone='+91 9777700000'
        )
        self.deal = Deal.objects.create(
            title='Won Deal For Report',
            customer=self.customer,
            assigned_to=self.admin,
            deal_value=Decimal('500000.00'),
            stage=Deal.Stage.WON,
            expected_closing_date='2026-10-01'
        )

    def test_reports_page_loads(self):
        self.client.login(username='admin_reports', password='Password123!')
        response = self.client.get(reverse('reports:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports & Analytics')
        self.assertContains(response, '500,000')

    def test_csv_export_endpoint(self):
        self.client.login(username='admin_reports', password='Password123!')
        response = self.client.get(reverse('reports:export_csv') + '?type=sales')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="smartcrm_sales_report', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Won Deal For Report', content)
        self.assertIn('500000.00', content)
