from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
import secrets
import string

from ..models import SchoolProfile, SchoolUser,SchoolAcademicYear
@login_required
def school_list(request):

    # -----------------------------------
    # SYSTEM SUPERUSER ONLY
    # -----------------------------------

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can view all schools."
        )
        return redirect("students:home")

    schools = (
        SchoolProfile.objects
        .all()
        .order_by("name")
    )

    return render(
        request,
        "students/school_list.html",
        {
            "schools": schools,
        },
    )

@login_required
def add_school_profile(request):

    # Only the system superuser can create schools
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can add a school."
        )
        return redirect("students:home")

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

        curriculum_system = request.POST.get(
                    "curriculum_system",
                    "CBC"
                    ).strip()

        valid_curriculum_systems = {
            "CBC",
            "8-4-4",
            "BOTH",
        }

        if curriculum_system not in valid_curriculum_systems:
            messages.error(
                request,
                "Please select a valid curriculum system."
            )
            return redirect("students:add_school_profile")
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
            return redirect("students:add_school_profile")

        if not admin_first_name:
            messages.error(
                request,
                "Administrator first name is required."
            )
            return redirect("students:add_school_profile")

        if not admin_last_name:
            messages.error(
                request,
                "Administrator last name is required."
            )
            return redirect("students:add_school_profile")

        if not admin_email:
            messages.error(
                request,
                "Administrator email is required."
            )
            return redirect("students:add_school_profile")

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
            curriculum_system=curriculum_system,

            principal_signature=request.FILES.get(
                "principal_signature"
            ),

            logo=request.FILES.get(
                "logo"
            ),
        )

        SchoolAcademicYear.objects.create(
            school=school,
            year=academic_year,
            is_current=True,
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

        return redirect("students:school_credentials")
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
        return redirect("students:home")

    credentials = request.session.pop(
        "new_school_credentials",
        None
    )

    if not credentials:
        messages.warning(
            request,
            "No new school credentials are available."
        )
        return redirect("students:home")

    return render(
        request,
        "students/school_credentials.html",
        {
            "credentials": credentials,
        },
    )

@login_required
def delete_school(request, id):

    # Only the system superuser can delete schools
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can delete a school."
        )
        return redirect("students:home")

    try:
        school = SchoolProfile.objects.get(id=id)
    except SchoolProfile.DoesNotExist:
        messages.error(
            request,
            "School not found."
        )
        return redirect("students:school_list")

    # -----------------------------------
    # PROTECT SCHOOLS WITH EXISTING DATA
    # -----------------------------------

    related_data = {
        "students": school.students.exists(),
        "teachers": school.teachers.exists(),
        "classes": school.classes.exists(),
        "users": school.users.exists(),
        "subjects": school.subjects.exists(),
        "fee ledger entries": school.ledger_entries.exists(),
    }

    existing_data = [
        name for name, exists in related_data.items()
        if exists
    ]

    if existing_data:
        messages.error(
            request,
            f"Cannot delete {school.name}. "
            f"The school has existing data: "
            f"{', '.join(existing_data)}."
        )
        return redirect("students:school_list")

    # -----------------------------------
    # DELETE EMPTY SCHOOL
    # -----------------------------------

    school_name = school.name
    school.delete()

    messages.success(
        request,
        f"{school_name} was deleted successfully."
    )

    return redirect("students:school_list")
@login_required
def reset_school_password(request, id):

    # -----------------------------------
    # SYSTEM SUPERUSER ONLY
    # -----------------------------------

    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can reset school passwords."
        )
        return redirect("students:home")

    # -----------------------------------
    # GET SCHOOL
    # -----------------------------------

    try:
        school = SchoolProfile.objects.get(id=id)
    except SchoolProfile.DoesNotExist:
        messages.error(
            request,
            "School not found."
        )
        return redirect("students:school_list")

    # -----------------------------------
    # GET SCHOOL ADMINISTRATOR
    # -----------------------------------

    school_user = (
        SchoolUser.objects
        .select_related("user")
        .filter(school=school)
        .first()
    )

    if not school_user:
        messages.error(
            request,
            f"No school user is associated with {school.name}."
        )
        return redirect("students:school_list")

    admin_user = school_user.user

    # -----------------------------------
    # RESET PASSWORD
    # -----------------------------------

    alphabet = string.ascii_letters + string.digits

    password = "".join(
        secrets.choice(alphabet)
        for _ in range(10)
    )

    admin_user.set_password(password)
    admin_user.save()

    # -----------------------------------
    # SHOW NEW CREDENTIALS
    # -----------------------------------

    request.session["new_school_credentials"] = {
        "school_name": school.name,
        "username": admin_user.username,
        "password": password,
        "email": admin_user.email,
    }

    return redirect("students:school_credentials")
