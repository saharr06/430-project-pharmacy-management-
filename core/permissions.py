from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "Manager"
    name = user.username.lower()
    for role in ("Manager", "Pharmacist", "Receptionist"):
        if name.startswith(role.lower()):
            return role
    return None


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if get_role(request.user) in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")
        return wrapper
    return decorator