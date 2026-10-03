import random
from django.db import models
from django.conf import settings


class Lead(models.Model):
    class Source(models.TextChoices):
        WEBSITE = 'Website', 'Website'
        INSTAGRAM = 'Instagram', 'Instagram'
        FACEBOOK = 'Facebook', 'Facebook'
        REFERRAL = 'Referral', 'Referral'
        OTHER = 'Other', 'Other'

    class Status(models.TextChoices):
        NEW = 'New', 'New'
        CONTACTED = 'Contacted', 'Contacted'
        INTERESTED = 'Interested', 'Interested'
        QUALIFIED = 'Qualified', 'Qualified'
        CONVERTED = 'Converted', 'Converted'
        LOST = 'Lost', 'Lost'

    class Priority(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'

    lead_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated unique lead identifier'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=150, blank=True)
    source = models.CharField(
        max_length=50,
        choices=Source.choices,
        default=Source.WEBSITE
    )
    interested_product = models.CharField(max_length=150, blank=True)
    estimated_deal_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Estimated deal value in INR (₹)'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    next_followup_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    lost_reason = models.TextField(blank=True)
    converted_customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead_id']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['source']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.lead_id} - {self.full_name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.lead_id:
            last = Lead.objects.filter(lead_id__startswith='LEAD-').order_by('-id').first()
            if last and last.lead_id:
                try:
                    num = int(last.lead_id.replace('LEAD-', '')) + 1
                    self.lead_id = f"LEAD-{num:05d}"
                except ValueError:
                    self.lead_id = f"LEAD-{random.randint(10000, 99999)}"
            else:
                self.lead_id = "LEAD-00101"
        super().save(*args, **kwargs)
