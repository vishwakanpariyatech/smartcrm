import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        MANAGER = 'Manager', 'Manager'
        EMPLOYEE = 'Employee', 'Employee'

    class Department(models.TextChoices):
        SALES = 'Sales', 'Sales'
        MARKETING = 'Marketing', 'Marketing'
        SUPPORT = 'Support', 'Customer Support'
        MANAGEMENT = 'Management', 'Management'
        OPERATIONS = 'Operations', 'Operations'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        help_text='User access level within CRM'
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text='Auto-generated unique employee ID'
    )
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(
        max_length=50,
        choices=Department.choices,
        default=Department.SALES,
        blank=True
    )
    joining_date = models.DateField(default=timezone.now, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full = self.get_full_name()
        return f"{full} ({self.role})" if full else f"{self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_manager_role(self):
        return self.role == self.Role.MANAGER

    @property
    def is_employee_role(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def display_name(self):
        name = self.get_full_name().strip()
        return name if name else self.username

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN

        if not self.employee_id:
            # Generate sequential/unique EMP-XXXX format
            last_user = User.objects.filter(employee_id__startswith='EMP-').order_by('-id').first()
            if last_user and last_user.employee_id:
                try:
                    num = int(last_user.employee_id.replace('EMP-', '')) + 1
                    self.employee_id = f"EMP-{num:04d}"
                except ValueError:
                    self.employee_id = f"EMP-{random.randint(1000, 9999)}"
            else:
                self.employee_id = "EMP-1001"
        super().save(*args, **kwargs)
