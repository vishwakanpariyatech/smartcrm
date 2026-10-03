from django import forms
from .models import FollowUp
from customers.models import Customer
from leads.models import Lead
from accounts.models import User


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = [
            'customer', 'lead', 'assigned_to', 'followup_date',
            'followup_time', 'followup_type', 'description', 'status', 'outcome'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'followup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'followup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'followup_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Meeting agenda, call discussion points, proposal walkthrough...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Result of conversation, client response, agreed next step...'}),
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


class FollowUpCompleteForm(forms.Form):
    outcome = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe what was discussed and the outcome...'}),
        required=True,
        label="Discussion Outcome"
    )
