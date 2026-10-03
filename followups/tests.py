from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer
from followups.models import FollowUp


class FollowUpManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='rep_followup',
            email='rep_flw@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        self.customer = Customer.objects.create(
            full_name='Followup Client',
            email='flwclient@test.com',
            phone='+91 9888800000',
            assigned_to=self.user
        )
        self.followup = FollowUp.objects.create(
            customer=self.customer,
            assigned_to=self.user,
            followup_date=date.today(),
            followup_type=FollowUp.Type.CALL,
            description='Call to discuss agreement terms',
            status=FollowUp.Status.PENDING
        )

    def test_auto_followup_id(self):
        self.assertTrue(self.followup.followup_id.startswith('FLW-'))

    def test_calendar_view_loads(self):
        self.client.login(username='rep_followup', password='Password123!')
        response = self.client.get(reverse('followups:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Follow-up Calendar')

    def test_complete_followup_records_outcome(self):
        self.client.login(username='rep_followup', password='Password123!')
        response = self.client.post(reverse('followups:complete', kwargs={'pk': self.followup.pk}), {
            'outcome': 'Spoke with CFO. Contract will be signed on Friday.'
        })
        self.assertEqual(response.status_code, 302)

        self.followup.refresh_from_db()
        self.assertEqual(self.followup.status, FollowUp.Status.COMPLETED)
        self.assertIn('Spoke with CFO', self.followup.outcome)
