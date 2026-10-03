import random
from django.db import models
from django.conf import settings
from django.utils import timezone


class FollowUp(models.Model):
    class Type(models.TextChoices):
        CALL = 'Call', 'Call'
        EMAIL = 'Email', 'Email'
        MEETING = 'Meeting', 'Meeting'
        OTHER = 'Other', 'Other'

    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    followup_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated follow-up ID'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followups'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followups'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followups'
    )
    followup_date = models.DateField(default=timezone.now)
    followup_time = models.TimeField(null=True, blank=True)
    followup_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.CALL
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    outcome = models.TextField(blank=True, help_text='Recorded outcome upon completion')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['followup_date', 'followup_time']
        indexes = [
            models.Index(fields=['followup_id']),
            models.Index(fields=['followup_date']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        target = self.customer or self.lead or "General"
        return f"{self.followup_id} - {self.followup_type} with {target} ({self.status})"

    @property
    def is_overdue(self):
        if self.status == self.Status.PENDING:
            return self.followup_date < timezone.now().date()
        return False

    @property
    def target_name(self):
        if self.customer:
            return f"Customer: {self.customer.full_name}"
        if self.lead:
            return f"Lead: {self.lead.full_name}"
        return "General"

    def save(self, *args, **kwargs):
        if not self.followup_id:
            last = FollowUp.objects.filter(followup_id__startswith='FLW-').order_by('-id').first()
            if last and last.followup_id:
                try:
                    num = int(last.followup_id.replace('FLW-', '')) + 1
                    self.followup_id = f"FLW-{num:05d}"
                except ValueError:
                    self.followup_id = f"FLW-{random.randint(10000, 99999)}"
            else:
                self.followup_id = "FLW-00101"
        super().save(*args, **kwargs)
