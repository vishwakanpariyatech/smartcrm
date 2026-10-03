from django import forms
from .models import Deal
from customers.models import Customer
from leads.models import Lead
from accounts.models import User


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'title', 'customer', 'lead', 'assigned_to', 'deal_value',
            'stage', 'expected_closing_date', 'actual_closing_date', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Enterprise CRM Annual Subscription'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'deal_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '150000.00'}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'expected_closing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_closing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deal scope, commercial terms, discounts, contract length...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name')
        if user and user.is_employee_role:
            self.fields['assigned_to'].initial = user
            self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
            self.fields['customer'].queryset = Customer.objects.filter(assigned_to=user)
            self.fields['lead'].queryset = Lead.objects.filter(assigned_to=user)
        else:
            self.fields['customer'].queryset = Customer.objects.all()
            self.fields['lead'].queryset = Lead.objects.all()
