from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer, CustomerNote


class CustomerCRUDAndPermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@crm.test',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.emp1 = User.objects.create_user(
            username='emp1_test',
            email='emp1@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        self.emp2 = User.objects.create_user(
            username='emp2_test',
            email='emp2@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )

        self.cust1 = Customer.objects.create(
            full_name='Customer Alpha',
            email='alpha@company.com',
            phone='+91 9800112233',
            company_name='Alpha Ltd',
            assigned_to=self.emp1
        )
        self.cust2 = Customer.objects.create(
            full_name='Customer Beta',
            email='beta@company.com',
            phone='+91 9800445566',
            company_name='Beta Ltd',
            assigned_to=self.emp2
        )

    def test_auto_customer_id(self):
        self.assertTrue(self.cust1.customer_id.startswith('CUST-'))

    def test_employee_scoped_customer_list(self):
        self.client.login(username='emp1_test', password='Password123!')
        response = self.client.get(reverse('customers:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer Alpha')
        self.assertNotContains(response, 'Customer Beta')

    def test_admin_sees_all_customers(self):
        self.client.login(username='admin_test', password='Password123!')
        response = self.client.get(reverse('customers:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer Alpha')
        self.assertContains(response, 'Customer Beta')

    def test_unauthorized_customer_detail_access_denied(self):
        # Emp1 tries to access cust2 (assigned to Emp2)
        self.client.login(username='emp1_test', password='Password123!')
        response = self.client.get(reverse('customers:detail', kwargs={'pk': self.cust2.pk}))
        self.assertEqual(response.status_code, 403)

    def test_authorized_customer_detail_success(self):
        self.client.login(username='emp1_test', password='Password123!')
        response = self.client.get(reverse('customers:detail', kwargs={'pk': self.cust1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer Alpha')

    def test_create_customer(self):
        self.client.login(username='emp1_test', password='Password123!')
        response = self.client.post(reverse('customers:create'), {
            'full_name': 'Customer Gamma',
            'email': 'gamma@company.com',
            'phone': '+91 9876500000',
            'company_name': 'Gamma Enterprises',
            'city': 'Mumbai',
            'source': 'Website',
            'status': 'Active',
            'assigned_to': self.emp1.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(email='gamma@company.com').exists())

    def test_add_customer_note(self):
        self.client.login(username='emp1_test', password='Password123!')
        response = self.client.post(reverse('customers:add_note', kwargs={'pk': self.cust1.pk}), {
            'content': 'Meeting completed. Client wants to sign next week.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomerNote.objects.filter(customer=self.cust1, content__contains='Meeting completed').exists())
