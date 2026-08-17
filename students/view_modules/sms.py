from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from students.models import (
    SMSMessage,
    SMSWallet,
)

from students.utils import get_user_school


@login_required
def sms_dashboard(request):

    # System administrator
    if request.user.is_superuser:
        return redirect("sms_add_credits")

    # School user
    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    wallet, created = SMSWallet.objects.get_or_create(
        school=school
    )

    total_sent = SMSMessage.objects.filter(
        school=school
    ).aggregate(
        total=Sum("sms_count")
    )["total"] or 0

    delivered = SMSMessage.objects.filter(
        school=school,
        status="delivered",
    ).aggregate(
        total=Sum("sms_count")
    )["total"] or 0

    failed = SMSMessage.objects.filter(
        school=school,
        status="failed",
    ).aggregate(
        total=Sum("sms_count")
    )["total"] or 0

    recent_sms = SMSMessage.objects.filter(
        school=school
    ).order_by(
        "-created_at"
    )[:10]

    context = {
        "school": school,
        "wallet": wallet,
        "total_sent": total_sent,
        "delivered": delivered,
        "failed": failed,
        "recent_sms": recent_sms,
    }

    return render(
        request,
        "sms/sms_dashboard.html",
        context,
    )