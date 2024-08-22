from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        decorated_view_func = user_passes_test(
            lambda user: user.is_authenticated and user.role in allowed_roles,
            login_url='login'
        )(view_func)
        return decorated_view_func
    return decorator