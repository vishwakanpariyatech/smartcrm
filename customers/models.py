import random
from django.db import models
from django.conf import settings


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    class Source(models.TextChoices):
        WEBSITE = 'Website', 'Website'
        REFERRAL = 'Referral', 'Referral'
        SOCIAL_MEDIA = 'Social Media', 'Social Media'
        DIRECT_OUTREACH = 'Direct Outreach', 'Direct Outreach'
        ADVERTISEMENT = 'Advertisement', 'Advertisement'
        OTHER = 'Other', 'Other'

    customer_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated unique customer identifier'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    source = models.CharField(
        max_length=50,
        choices=Source.choices,
        default=Source.WEBSITE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['city']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.customer_id} - {self.full_name} ({self.company_name or 'Individual'})"

    def save(self, *args, **kwargs):
        if not self.customer_id:
            last = Customer.objects.filter(customer_id__startswith='CUST-').order_by('-id').first()
            if last and last.customer_id:
                try:
                    num = int(last.customer_id.replace('CUST-', '')) + 1
                    self.customer_id = f"CUST-{num:05d}"
                except ValueError:
                    self.customer_id = f"CUST-{random.randint(10000, 99999)}"
            else:
                self.customer_id = "CUST-00101"
        super().save(*args, **kwargs)


class CustomerNote(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.customer.customer_id} by {self.author or 'Unknown'}"
