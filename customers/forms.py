from django import forms
from .models import Customer, CustomerNote
from accounts.models import User


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'full_name', 'email', 'phone', 'company_name',
            'address', 'city', 'state', 'postal_code',
            'source', 'status', 'assigned_to', 'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rahul Sharma'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'rahul@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Acme Corp Pvt Ltd'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address, office suite'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mumbai'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maharashtra'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '400001'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional context, preferences, or account notes'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_to choices to active employees
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        # If current user is an employee and not manager/admin, default/lock assignment
        if user and user.is_employee_role:
            self.fields['assigned_to'].initial = user
            # Non-admin/manager can only assign to themselves
            self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)


class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write an account note or interaction summary...'})
        }
