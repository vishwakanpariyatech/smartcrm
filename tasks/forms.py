from django import forms
from .models import Task
from customers.models import Customer
from leads.models import Lead
from accounts.models import User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'customer', 'lead',
            'priority', 'status', 'start_date', 'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Schedule product demonstration'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Specific objectives, checklist, or instructions...'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
