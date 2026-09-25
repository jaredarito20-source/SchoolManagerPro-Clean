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
        lambda u: u.is_superuser or u.groups.filter(name="Bursar").exists()
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
        u.groups.filter(name="Head Teacher").exists() or
        u.groups.filter(name="Teachers").exists()
    )(view_func)

    return decorated_view

def admin_or_bursar(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_superuser or
        u.groups.filter(name="Administrators").exists() or
        u.groups.filter(name="Bursar").exists()
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



def in_group(*groups):
    def decorator(view_func):
        return user_passes_test(
            lambda u: u.is_authenticated and (
                u.is_superuser or
                u.groups.filter(name__in=groups).exists()
            )
        )(view_func)
    return decorator

# ============================================================
# SUBSCRIPTION TIER ACCESS
# ============================================================

SUBSCRIPTION_TIER_LEVELS = {
    "T1": 1,
    "T2": 2,
    "T3": 3,
    "T4": 4,
    "T5": 5,
    "T6": 6,
}


def user_has_subscription_tier(user, required_tier):
    """
    Check whether the user's school subscription includes
    the required cumulative tier.

    Superusers have unrestricted access.

    Subscription access is separate from role/group permissions.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        school = user.school_user.school
    except (AttributeError, SchoolUser.DoesNotExist):
        return False

    current_level = SUBSCRIPTION_TIER_LEVELS.get(
        school.subscription_tier,
        0,
    )

    required_level = SUBSCRIPTION_TIER_LEVELS.get(
        required_tier,
        0,
    )

    if required_level == 0:
        return False

    return current_level >= required_level

def subscription_required(required_tier):
    """
    Restrict a view according to the school's subscription tier.

    Tier access is cumulative:
        T1 -> T1
        T2 -> T1 + T2
        T3 -> T1 + T2 + T3
        ...
        T6 -> all tiers

    Superusers are unrestricted.
    """

    def decorator(view_func):
        return user_passes_test(
            lambda u: user_has_subscription_tier(
                u,
                required_tier,
            )
        )(view_func)

    return decorator


SUBSCRIPTION_MODULE_TIERS = {
    # --------------------------------------------------------
    # TIER 1
    # --------------------------------------------------------
    "academic": "T1",
    "parents": "T1",
    "sms": "T1",

    # --------------------------------------------------------
    # TIER 2
    # --------------------------------------------------------
    "finance": "T2",

    # --------------------------------------------------------
    # TIER 3
    # --------------------------------------------------------
    "transport": "T3",

    # --------------------------------------------------------
    # TIER 4
    # --------------------------------------------------------
    "attendance": "T4",
    "homework": "T4",
    "hostel": "T4",
    "discipline": "T4",
    "medical": "T4",

    # --------------------------------------------------------
    # TIER 5
    # --------------------------------------------------------
    "library": "T5",
    "inventory": "T5",

    # --------------------------------------------------------
    # TIER 6
    # --------------------------------------------------------
    "payroll": "T6",
    "administration": "T6",
}

def user_has_module_access(user, module_name):
    """
    Check whether the user's school subscription includes
    the requested module.

    Module access is cumulative according to the school's
    subscription tier.

    Superusers have unrestricted access.
    """

    required_tier = SUBSCRIPTION_MODULE_TIERS.get(module_name)

    if required_tier is None:
        return False

    return user_has_subscription_tier(
        user,
        required_tier,
    )