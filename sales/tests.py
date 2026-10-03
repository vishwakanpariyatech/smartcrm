from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.db.models import Sum
from accounts.models import User
from customers.models import Customer
from sales.models import Deal


class SalesAndDealRevenueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp = User.objects.create_user(
            username='sales_rep',
            email='rep@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        self.customer = Customer.objects.create(
            full_name='Test Client',
            email='client@test.com',
            phone='+91 9999900000',
            assigned_to=self.emp
        )
        self.deal1 = Deal.objects.create(
            title='Software Deal A',
            customer=self.customer,
            assigned_to=self.emp,
            deal_value=Decimal('100000.00'),
            stage=Deal.Stage.WON,
            expected_closing_date='2026-10-15'
        )
        self.deal2 = Deal.objects.create(
            title='Software Deal B',
            customer=self.customer,
            assigned_to=self.emp,
            deal_value=Decimal('200000.00'),
            stage=Deal.Stage.PROPOSAL,
            expected_closing_date='2026-11-15'
        )

    def test_auto_deal_id(self):
        self.assertTrue(self.deal1.deal_id.startswith('DEAL-'))

    def test_revenue_calculated_strictly_from_won_deals(self):
        won_revenue = Deal.objects.filter(stage=Deal.Stage.WON).aggregate(v=Sum('deal_value'))['v']
        self.assertEqual(won_revenue, Decimal('100000.00'))

    def test_won_stage_sets_actual_closing_date(self):
        self.assertIsNotNone(self.deal1.actual_closing_date)
        self.assertIsNone(self.deal2.actual_closing_date)

    def test_deal_stage_change_prevents_double_counting(self):
        # Mark deal 2 as Won
        self.client.login(username='sales_rep', password='Password123!')
        response = self.client.post(reverse('sales:mark_stage', kwargs={'pk': self.deal2.pk}), {
            'stage': 'Won'
        })
        self.assertEqual(response.status_code, 302)
        self.deal2.refresh_from_db()
        self.assertEqual(self.deal2.stage, Deal.Stage.WON)

        won_revenue = Deal.objects.filter(stage=Deal.Stage.WON).aggregate(v=Sum('deal_value'))['v']
        self.assertEqual(won_revenue, Decimal('300000.00'))

        # Now mark deal 1 as Lost -> won revenue should decrease back
        self.client.post(reverse('sales:mark_stage', kwargs={'pk': self.deal1.pk}), {
            'stage': 'Lost'
        })
        self.deal1.refresh_from_db()
        self.assertEqual(self.deal1.stage, Deal.Stage.LOST)
        won_revenue_after = Deal.objects.filter(stage=Deal.Stage.WON).aggregate(v=Sum('deal_value'))['v']
        self.assertEqual(won_revenue_after, Decimal('200000.00'))
