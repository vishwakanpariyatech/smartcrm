from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer
from leads.models import Lead
from sales.models import Deal


class LeadCRUDAndConversionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_lead',
            email='admin_lead@crm.test',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.emp1 = User.objects.create_user(
            username='emp1_lead',
            email='emp1_lead@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        self.emp2 = User.objects.create_user(
            username='emp2_lead',
            email='emp2_lead@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )

        self.lead1 = Lead.objects.create(
            full_name='Prospect One',
            email='prospect1@startup.io',
            phone='+91 9100110011',
            company='Startup One',
            estimated_deal_value=Decimal('150000.00'),
            status=Lead.Status.QUALIFIED,
            assigned_to=self.emp1
        )
        self.lead2 = Lead.objects.create(
            full_name='Prospect Two',
            email='prospect2@startup.io',
            phone='+91 9100220022',
            company='Startup Two',
            estimated_deal_value=Decimal('80000.00'),
            status=Lead.Status.NEW,
            assigned_to=self.emp2
        )

    def test_auto_lead_id(self):
        self.assertTrue(self.lead1.lead_id.startswith('LEAD-'))

    def test_employee_scoped_lead_list(self):
        self.client.login(username='emp1_lead', password='Password123!')
        response = self.client.get(reverse('leads:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prospect One')
        self.assertNotContains(response, 'Prospect Two')

    def test_unauthorized_lead_detail_denied(self):
        self.client.login(username='emp1_lead', password='Password123!')
        response = self.client.get(reverse('leads:detail', kwargs={'pk': self.lead2.pk}))
        self.assertEqual(response.status_code, 403)

    def test_lead_conversion_workflow(self):
        self.client.login(username='emp1_lead', password='Password123!')
        response = self.client.post(reverse('leads:convert', kwargs={'pk': self.lead1.pk}), {
            'create_deal': True,
            'deal_title': 'Enterprise License for Prospect One',
            'deal_value': '150000.00',
            'expected_closing_date': '2026-12-31'
        })
        self.assertEqual(response.status_code, 302)

        # Refresh lead
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, Lead.Status.CONVERTED)
        self.assertIsNotNone(self.lead1.converted_customer)
        self.assertEqual(self.lead1.converted_customer.email, 'prospect1@startup.io')

        # Check deal was created
        deal = Deal.objects.filter(lead=self.lead1).first()
        self.assertIsNotNone(deal)
        self.assertEqual(deal.deal_value, Decimal('150000.00'))

    def test_pipeline_stage_update(self):
        self.client.login(username='emp1_lead', password='Password123!')
        response = self.client.post(reverse('leads:update_stage', kwargs={'pk': self.lead1.pk}), {
            'status': 'Contacted'
        })
        self.assertEqual(response.status_code, 302)
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, 'Contacted')
