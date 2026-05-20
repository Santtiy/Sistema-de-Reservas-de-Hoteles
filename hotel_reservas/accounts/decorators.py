from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return redirect("home")

        return _wrapped

    return decorator


def admin_required(view_func):
    return role_required(["ADMIN"])(view_func)


def cliente_required(view_func):
    return role_required(["CLIENTE"])(view_func)


def recepcionista_required(view_func):
    return role_required(["RECEPCIONISTA"])(view_func)
