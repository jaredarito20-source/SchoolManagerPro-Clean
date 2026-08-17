from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from students.models import SchoolProfile, SMSWallet, SMSTransaction,SMSPackage
from students.utils import get_user_school
import uuid
from students.models import SMSPackage, SMSPurchase
from students.utils import get_user_school






@login_required
def sms_add_credits(request):

    # Only the main system administrator can add SMS credits
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can add SMS credits."
        )
        return redirect("home")

    schools = SchoolProfile.objects.all().order_by("name")

    if request.method == "POST":

        school_id = request.POST.get("school")
        quantity = request.POST.get("quantity", "").strip()

        if not school_id:
            messages.error(
                request,
                "Please select a school."
            )
            return redirect("sms_add_credits")

        if not quantity:
            messages.error(
                request,
                "Please enter the number of SMS credits."
            )
            return redirect("sms_add_credits")

        try:
            quantity = int(quantity)
        except ValueError:
            messages.error(
                request,
                "SMS credits must be a whole number."
            )
            return redirect("sms_add_credits")

        if quantity <= 0:
            messages.error(
                request,
                "SMS credits must be greater than zero."
            )
            return redirect("sms_add_credits")

        school = get_object_or_404(
            SchoolProfile,
            id=school_id,
        )

        wallet, created = SMSWallet.objects.get_or_create(
            school=school
        )

        wallet.balance += quantity
        wallet.save()

        SMSTransaction.objects.create(
            school=school,
            transaction_type="purchase",
            quantity=quantity,
            balance_after=wallet.balance,
            description=f"SMS credits added to {school.name}",
            created_by=request.user,
        )

        messages.success(
            request,
            f"{quantity:,} SMS credits added to {school.name}."
        )

        return redirect("sms_add_credits")

    return render(
        request,
        "sms/sms_add_credits.html",
        {
            "schools": schools,
        },
    )


def sms_packages(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    packages = SMSPackage.objects.filter(
        active=True
    ).order_by("price")

    return render(
        request,
        "sms/sms_packages.html",
        {
            "school": school,
            "packages": packages,
        },
    )



@login_required
def sms_buy_package(request, package_id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    package = get_object_or_404(
        SMSPackage,
        id=package_id,
        active=True,
    )

    reference = "SMS-" + uuid.uuid4().hex[:12].upper()

    purchase = SMSPurchase.objects.create(
        school=school,
        package=package,
        amount=package.price,
        sms_count=package.sms_count,
        status="Pending",
        reference=reference,
        created_by=request.user,
    )

    return redirect(
        "sms_checkout",
        purchase_id=purchase.id,
    )

@login_required
def sms_checkout(request, purchase_id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    purchase = get_object_or_404(
        SMSPurchase,
        id=purchase_id,
        school=school,
        status="Pending",
    )

    return render(
        request,
        "sms/sms_checkout.html",
        {
            "school": school,
            "purchase": purchase,
        },
    )