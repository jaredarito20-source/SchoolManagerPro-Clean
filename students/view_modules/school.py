from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
import secrets
import string

from ..models import SchoolProfile, SchoolUser

@login_required
def add_school_profile(request):

    # Only the system superuser can create schools
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can add a school."
        )
        return redirect("home")

    if request.method == "POST":

        # --------------------------------
        # SCHOOL DETAILS
        # --------------------------------

        name = request.POST.get("name", "").strip()
        motto = request.POST.get("motto", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        website = request.POST.get("website", "").strip()
        current_term = request.POST.get(
            "current_term",
            ""
        ).strip()
        academic_year = request.POST.get(
            "academic_year",
            ""
        ).strip()
        principal_name = request.POST.get(
            "principal_name",
            ""
        ).strip()

        # --------------------------------
        # FIRST ADMINISTRATOR DETAILS
        # --------------------------------

        admin_first_name = request.POST.get(
            "admin_first_name",
            ""
        ).strip()

        admin_last_name = request.POST.get(
            "admin_last_name",
            ""
        ).strip()

        admin_email = request.POST.get(
            "admin_email",
            ""
        ).strip().lower()

        # --------------------------------
        # BASIC VALIDATION
        # --------------------------------

        if not name:
            messages.error(
                request,
                "School name is required."
            )
            return redirect("add_school_profile")

        if not admin_first_name:
            messages.error(
                request,
                "Administrator first name is required."
            )
            return redirect("add_school_profile")

        if not admin_last_name:
            messages.error(
                request,
                "Administrator last name is required."
            )
            return redirect("add_school_profile")

        if not admin_email:
            messages.error(
                request,
                "Administrator email is required."
            )
            return redirect("add_school_profile")

        # --------------------------------
        # CHECK SCHOOL
        # --------------------------------

        if SchoolProfile.objects.filter(
            name__iexact=name
        ).exists():

            messages.error(
                request,
                "A school with this name already exists."
            )

            return redirect(
                "add_school_profile"
            )

        # --------------------------------
        # CHECK ADMIN EMAIL
        # --------------------------------

        if User.objects.filter(
            email__iexact=admin_email
        ).exists():

            messages.error(
                request,
                "A user with this email already exists."
            )

            return redirect(
                "add_school_profile"
            )

        # --------------------------------
        # CREATE SCHOOL
        # --------------------------------

        school = SchoolProfile.objects.create(
            name=name,
            motto=motto,
            address=address,
            phone=phone,
            email=email,
            website=website,
            current_term=current_term,
            academic_year=academic_year,
            principal_name=principal_name,

            principal_signature=request.FILES.get(
                "principal_signature"
            ),

            logo=request.FILES.get(
                "logo"
            ),
        )

        # --------------------------------
        # GENERATE USERNAME
        # --------------------------------

        base_username = (
            admin_first_name.lower()
            + "."
            + admin_last_name.lower()
        )

        base_username = (
            base_username
            .replace(" ", "")
        )

        username = base_username

        counter = 1

        while User.objects.filter(
            username=username
        ).exists():

            username = (
                f"{base_username}{counter}"
            )

            counter += 1

        # --------------------------------
        # GENERATE TEMPORARY PASSWORD
        # --------------------------------

        alphabet = string.ascii_letters + string.digits

        password = "".join(
                secrets.choice(alphabet)
                for _ in range(10)
            )

        # --------------------------------
        # CREATE USER
        # --------------------------------

        admin_user = User.objects.create_user(
            username=username,
            email=admin_email,
            password=password,
            first_name=admin_first_name,
            last_name=admin_last_name,
        )

        # --------------------------------
        # CREATE SCHOOL USER LINK
        # --------------------------------

        SchoolUser.objects.create(
            user=admin_user,
            school=school,
        )

        # --------------------------------
        # ADD ADMINISTRATOR GROUP
        # --------------------------------

        administrator_group = Group.objects.filter(
            name="Administrators"
        ).first()

        if administrator_group:

            admin_user.groups.add(
                administrator_group
            )

        # --------------------------------
        # SUCCESS
        # --------------------------------

        messages.success(
            request,
            f"School '{school.name}' created successfully."
        )

        # Store credentials temporarily
        request.session["new_school_credentials"] = {
            "school_name": school.name,
            "username": username,
            "password": password,
            "email": admin_email,
        }

        return redirect(
            "school_credentials"
        )

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/add_school_profile.html",
    )

@login_required
def school_credentials(request):

    # Only the system administrator can see newly
    # generated school credentials.
    if not request.user.is_superuser:
        messages.error(
            request,
            "You are not authorized to view school credentials."
        )
        return redirect("home")

    credentials = request.session.pop(
        "new_school_credentials",
        None
    )

    if not credentials:
        messages.warning(
            request,
            "No new school credentials are available."
        )
        return redirect("home")

    return render(
        request,
        "students/school_credentials.html",
        {
            "credentials": credentials,
        },
    )