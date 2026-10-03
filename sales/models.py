import random
from django.db import models
from django.conf import settings
from django.utils import timezone


class Deal(models.Model):
    class Stage(models.TextChoices):
        NEW = 'New', 'New'
        PROPOSAL = 'Proposal', 'Proposal'
        NEGOTIATION = 'Negotiation', 'Negotiation'
        WON = 'Won', 'Won'
        LOST = 'Lost', 'Lost'

    deal_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated unique deal identifier'
    )
    title = models.CharField(max_length=200)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='deals'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deals'
    )
    deal_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Deal value in INR (₹)'
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.NEW
    )
    expected_closing_date = models.DateField()
    actual_closing_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deal_id']),
            models.Index(fields=['stage']),
            models.Index(fields=['expected_closing_date']),
            models.Index(fields=['assigned_to', 'stage']),
        ]

    def __str__(self):
        return f"{self.deal_id} - {self.title} (₹{self.deal_value:,.2f}) [{self.stage}]"

    def save(self, *args, **kwargs):
        if not self.deal_id:
            last = Deal.objects.filter(deal_id__startswith='DEAL-').order_by('-id').first()
            if last and last.deal_id:
                try:
                    num = int(last.deal_id.replace('DEAL-', '')) + 1
                    self.deal_id = f"DEAL-{num:05d}"
                except ValueError:
                    self.deal_id = f"DEAL-{random.randint(10000, 99999)}"
            else:
                self.deal_id = "DEAL-00101"

        if self.stage == self.Stage.WON and not self.actual_closing_date:
            self.actual_closing_date = timezone.now().date()
        elif self.stage != self.Stage.WON and self.stage != self.Stage.LOST:
            self.actual_closing_date = None

        super().save(*args, **kwargs)
