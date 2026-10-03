from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        self.employee_user = User.objects.create_user(
            username='testemp',
            email='emp@test.com',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )

    def test_auto_generated_employee_id(self):
        self.assertTrue(self.admin_user.employee_id.startswith('EMP-'))
        self.assertTrue(self.employee_user.employee_id.startswith('EMP-'))

    def test_role_properties(self):
        self.assertTrue(self.admin_user.is_admin_role)
        self.assertFalse(self.admin_user.is_employee_role)
        self.assertTrue(self.employee_user.is_employee_role)
        self.assertFalse(self.employee_user.is_admin_role)

    def test_successful_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testemp',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_failed_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testemp',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_inactive_user_cannot_login(self):
        self.employee_user.is_active = False
        self.employee_user.save()

        response = self.client.post(reverse('accounts:login'), {
            'username': 'testemp',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This account has been deactivated")

    def test_profile_view_requires_auth(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='testemp', password='Password123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testemp")

    def test_successful_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newemployee',
            'email': 'newemployee@example.com',
            'first_name': 'New',
            'last_name': 'Employee',
            'department': 'Support',
            'phone': '9876543210',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123'
        })
        self.assertRedirects(response, reverse('accounts:login'))
        created = User.objects.filter(username='newemployee').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.role, User.Role.EMPLOYEE)
        self.assertTrue(created.is_active)
        self.assertTrue(created.check_password('SecurePassword123'))

    def test_registration_validation_errors(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'testadmin',  # duplicate
            'email': 'admin@test.com',  # duplicate
            'password': 'short',  # < 8
            'confirm_password': 'mismatch'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")
        self.assertContains(response, "already exists")
        self.assertContains(response, "Passwords do not match")
