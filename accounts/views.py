from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.conf import settings
from .forms import LoginForm, UserProfileForm, EmployeeCreateForm, RegistrationForm
from .models import User
from activity_logs.models import log_activity


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "This account has been deactivated. Please contact your CRM administrator.")
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            log_activity(user, 'Logged in', 'User', user.id, user.display_name, 'Successful authentication')
            messages.success(request, f"Welcome back, {user.display_name}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            username = request.POST.get('username')
            user_candidate = User.objects.filter(username=username).first() or User.objects.filter(email=username).first()
            if user_candidate and not user_candidate.is_active and user_candidate.check_password(request.POST.get('password')):
                messages.error(request, "This account has been deactivated. Please contact your CRM administrator.")
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, 'Logged out', 'User', request.user.id, request.user.display_name)
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    context = {
        'user_obj': user,
        'assigned_customers_count': user.customers.count() if hasattr(user, 'customers') else 0,
        'assigned_leads_count': user.leads.count() if hasattr(user, 'leads') else 0,
        'pending_tasks_count': user.assigned_tasks.filter(status__in=['Pending', 'In Progress']).count() if hasattr(user, 'assigned_tasks') else 0,
        'won_deals_count': user.deals.filter(stage='Won').count() if hasattr(user, 'deals') else 0,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            log_activity(user, 'Updated profile', 'User', user.id, user.display_name)
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(user, 'Changed password', 'User', user.id, user.display_name)
            messages.success(request, "Your password has been changed successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def settings_view(request):
    context = {
        'app_name': 'SmartCRM Enterprise',
        'currency': 'INR (₹)',
        'timezone': settings.TIME_ZONE,
        'date_format': 'DD-MM-YYYY',
        'db_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'email_backend': settings.EMAIL_BACKEND.split('.')[-1],
    }
    return render(request, 'accounts/settings.html', context)


def register_view(request):
    """
    Public registration page providing initial onboarding guidance.
    In enterprise CRM, employee creation is typically managed by Admins,
    but this provides a self-service signup or redirect to demo credentials.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, 'Self-registered', 'User', user.id, user.display_name)
            messages.success(request, f"Welcome to SmartCRM! Account '{user.username}' created successfully. Please sign in.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Registration failed. Please check the errors highlighted below.")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})
