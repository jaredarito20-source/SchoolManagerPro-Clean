from django.contrib.auth.decorators import user_passes_test


def admin_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or u.groups.filter(name="Administrators").exists()
    )(view_func)
    return decorated_view


def teacher_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or u.groups.filter(name="Teachers").exists()
    )(view_func)
    return decorated_view


def bursar_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or u.groups.filter(name="Bursars").exists()
    )(view_func)
    return decorated_view


def secretary_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or u.groups.filter(name="Secretaries").exists()
    )(view_func)
    return decorated_view


def admin_or_teacher(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or
        u.groups.filter(name="Administrators").exists() or
        u.groups.filter(name="Teachers").exists()
    )(view_func)
    return decorated_view


def admin_or_bursar(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or
        u.groups.filter(name="Administrators").exists() or
        u.groups.filter(name="Bursars").exists()
    )(view_func)
    return decorated_view


def admin_teacher_secretary(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or
        u.groups.filter(name="Administrators").exists() or
        u.groups.filter(name="Teachers").exists() or
        u.groups.filter(name="Secretaries").exists()
    )(view_func)
    return decorated_view