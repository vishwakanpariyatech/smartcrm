from django import forms
from .models import Lead
from accounts.models import User


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'full_name', 'email', 'phone', 'company', 'source',
            'interested_product', 'estimated_deal_value', 'status',
            'priority', 'assigned_to', 'next_followup_date', 'notes', 'lost_reason'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sneha Patel'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'sneha@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9812345678'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TechSolutions Ltd'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'interested_product': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Cloud ERP Software'}),
            'estimated_deal_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '50000.00'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'next_followup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Initial inquiry summary, requirements...'}),
            'lost_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason if lead status is Lost...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name')
        if user and user.is_employee_role:
            self.fields['assigned_to'].initial = user
            self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)


class ConvertLeadForm(forms.Form):
    create_deal = forms.BooleanField(required=False, initial=True, label="Create an initial Deal in Sales pipeline")
    deal_title = forms.CharField(max_length=200, required=False, label="Deal Title")
    deal_value = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label="Deal Value (₹)")
    expected_closing_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Target Closing Date")
