import random
from django.db import models
from django.conf import settings
from django.utils import timezone


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        URGENT = 'Urgent', 'Urgent'

    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        IN_PROGRESS = 'In Progress', 'In Progress'
        COMPLETED = 'Completed', 'Completed'

    task_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated unique task identifier'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    start_date = models.DateField(default=timezone.now, null=True, blank=True)
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.task_id} - {self.title} ({self.status})"

    @property
    def is_overdue(self):
        if self.status != self.Status.COMPLETED and self.due_date:
            return self.due_date < timezone.now().date()
        return False

    def save(self, *args, **kwargs):
        if not self.task_id:
            last = Task.objects.filter(task_id__startswith='TSK-').order_by('-id').first()
            if last and last.task_id:
                try:
                    num = int(last.task_id.replace('TSK-', '')) + 1
                    self.task_id = f"TSK-{num:05d}"
                except ValueError:
                    self.task_id = f"TSK-{random.randint(10000, 99999)}"
            else:
                self.task_id = "TSK-00101"

        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completed_at = None

        super().save(*args, **kwargs)
