from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)

            raise PermissionDenied(
                "You do not have permission to access this page."
            )

        return wrapper
    return decorator