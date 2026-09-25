from students.decorators import user_has_module_access


def subscription_access(request):
    """
    Expose subscription-module access to templates.
    """

    if not request.user.is_authenticated:
        return {
            "subscription_access": {},
        }

    modules = [
        "academic",
        "parents",
        "sms",
        "finance",
        "transport",
        "attendance",
        "homework",
        "hostel",
        "discipline",
        "medical",
        "library",
        "inventory",
        "payroll",
        "administration",
    ]

    return {
        "subscription_access": {
            module: user_has_module_access(
                request.user,
                module,
            )
            for module in modules
        }
    }
