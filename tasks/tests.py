from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from tasks.models import Task


class TaskManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='task_worker',
            email='worker@crm.test',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        today = timezone.now().date()
        self.overdue_task = Task.objects.create(
            title='Overdue Task Example',
            assigned_to=self.user,
            due_date=today - timedelta(days=5),
            status=Task.Status.PENDING
        )
        self.future_task = Task.objects.create(
            title='Future Task Example',
            assigned_to=self.user,
            due_date=today + timedelta(days=5),
            status=Task.Status.PENDING
        )

    def test_auto_task_id(self):
        self.assertTrue(self.overdue_task.task_id.startswith('TSK-'))

    def test_overdue_property(self):
        self.assertTrue(self.overdue_task.is_overdue)
        self.assertFalse(self.future_task.is_overdue)

    def test_toggle_complete_task(self):
        self.client.login(username='task_worker', password='Password123!')
        response = self.client.post(reverse('tasks:toggle_complete', kwargs={'pk': self.overdue_task.pk}))
        self.assertEqual(response.status_code, 302)

        self.overdue_task.refresh_from_db()
        self.assertEqual(self.overdue_task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.overdue_task.completed_at)
        self.assertFalse(self.overdue_task.is_overdue)  # Completed task is no longer overdue
