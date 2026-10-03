from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has one of the allowed roles.
    Superusers automatically pass.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this resource.")
            raise PermissionDenied("You do not have required role permissions.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['Admin'])(view_func)


def manager_or_admin_required(view_func):
    return role_required(['Admin', 'Manager'])(view_func)


class RoleRequiredMixin(AccessMixin):
    """CBV Mixin to verify that the current user has the required CRM role."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser or request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "Access denied. Insufficient permissions.")
        raise PermissionDenied("Access denied. Insufficient permissions.")


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['Admin']


class ManagerOrAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['Admin', 'Manager']
