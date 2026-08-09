from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum




import os
import shutil


from django.conf import settings

from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from students.decorators import admin_or_bursar

from django.contrib.auth.models import Group




from students.decorators import admin_or_bursar

from django.contrib.auth.models import User




from students.decorators import admin_or_bursar

from reportlab.pdfgen import canvas

from students.models import *

from students.decorators import (
    admin_or_bursar,
    in_group,
)

from students.utils import (
    draw_school_header,
    draw_school_footer,
)



from students.models import (
    SchoolClass,
    SubjectRequirement,
    TeacherAvailability,
    SchoolDay,
    Period,
    Timetable,
)

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Teachers",
    "Bursar",
    "Secretaries",
)


def is_admin(user):
    return (
        user.is_superuser or
        user.groups.filter(name="Administrators").exists()
    )


def is_teacher(user):
    return user.groups.filter(name="Teachers").exists()


def is_bursar(user):
    return user.groups.filter(name="Bursar").exists()


def is_secretary(user):
    return user.groups.filter(name="Secretaries").exists()










@login_required
def home(request):
    user = request.user

    if user.is_superuser or user.groups.filter(name="Administrators").exists():
        return render(request, "students/home.html")

    elif user.groups.filter(name="Teachers").exists():
        return render(request, "students/home.html")

    elif user.groups.filter(name="Bursar").exists():
        return render(request, "students/home.html")

    elif user.groups.filter(name="Parents").exists():
        return redirect("parent_dashboard")

    elif user.groups.filter(name="Head Teacher").exists():
        return render(request, "home.html")

    elif user.groups.filter(name="Secretaries").exists():
        return render(request, "home.html")

    # Default for authenticated users
    return render(request, "students/home.html")
@login_required
@admin_or_bursar
def school_profile(request):
    profile = SchoolProfile.objects.first()

    return render(
        request,
        "students/school_profile.html",
        {
            "profile": profile,
        },
    )


@login_required
@admin_or_bursar
def edit_school_profile(request):
    profile = SchoolProfile.objects.first()

    if not profile:
        profile = SchoolProfile.objects.create(
            school_name="My School",
        )

    if request.method == "POST":

        profile.school_name = request.POST["school_name"]
        profile.motto = request.POST["motto"]
        profile.address = request.POST["address"]
        profile.phone = request.POST["phone"]
        profile.email = request.POST["email"]
        profile.website = request.POST["website"]
        profile.principal = request.POST["principal"]

        if request.FILES.get("logo"):
            profile.logo = request.FILES["logo"]

        profile.save()

        messages.success(
            request,
            "School profile updated successfully.",
        )

        return redirect("school_profile")

    return render(
        request,
        "students/edit_school_profile.html",
        {
            "profile": profile,
        },
    )

@login_required
@admin_or_bursar
def settings(request):
    return render(
        request,
        "students/settings.html",
    )


@login_required
@admin_or_bursar
def system_settings(request):

    profile = SchoolProfile.objects.first()

    if request.method == "POST":

        profile.school_name = request.POST.get("school_name")
        profile.motto = request.POST.get("motto")
        profile.address = request.POST.get("address")
        profile.phone = request.POST.get("phone")
        profile.email = request.POST.get("email")
        profile.website = request.POST.get("website")

        if request.FILES.get("logo"):
            profile.logo = request.FILES["logo"]

        profile.save()

        messages.success(
            request,
            "System settings updated successfully.",
        )

        return redirect("system_settings")

    return render(
        request,
        "students/system_settings.html",
        {
            "profile": profile,
        },
    )

@login_required
@admin_or_bursar
def user_list(request):

    users = User.objects.all().order_by("username")

    return render(
        request,
        "students/user_list.html",
        {
            "users": users,
        },
    )
@login_required
@admin_or_bursar
def add_user(request):

    if request.method == "POST":

        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                "Username already exists.",
            )

            return redirect("add_user")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(
            request,
            "User created successfully.",
        )

        return redirect("user_list")

    return render(
        request,
        "students/add_user.html",
    )
@login_required
@admin_or_bursar
def edit_user(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id,
    )

    if request.method == "POST":

        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.email = request.POST["email"]

        if request.POST.get("password"):

            user.set_password(
                request.POST["password"]
            )

        user.save()

        messages.success(
            request,
            "User updated successfully.",
        )

        return redirect("user_list")

    return render(
        request,
        "students/edit_user.html",
        {
            "user": user,
        },
    )
@login_required
@admin_or_bursar
def delete_user(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id,
    )

    if request.method == "POST":

        user.delete()

        messages.success(
            request,
            "User deleted successfully.",
        )

        return redirect("user_list")

    return render(
        request,
        "students/delete_user.html",
        {
            "user": user,
        },
    )

@login_required
@admin_or_bursar
def role_list(request):

    roles = Group.objects.all().order_by("name")

    return render(
        request,
        "students/role_list.html",
        {
            "roles": roles,
        },
    )

@login_required
@admin_or_bursar
def add_role(request):

    if request.method == "POST":

        name = request.POST["name"].strip()

        if Group.objects.filter(name=name).exists():

            messages.error(
                request,
                "Role already exists.",
            )

            return redirect("add_role")

        Group.objects.create(
            name=name,
        )

        messages.success(
            request,
            "Role created successfully.",
        )

        return redirect("role_list")

    return render(
        request,
        "students/add_role.html",
    )

@login_required
@admin_or_bursar
def edit_role(request, role_id):

    role = get_object_or_404(
        Group,
        id=role_id,
    )

    if request.method == "POST":

        name = request.POST["name"].strip()

        if (
            Group.objects.filter(name=name)
            .exclude(id=role.id)
            .exists()
        ):

            messages.error(
                request,
                "Role already exists.",
            )

            return redirect(
                "edit_role",
                role_id=role.id,
            )

        role.name = name
        role.save()

        messages.success(
            request,
            "Role updated successfully.",
        )

        return redirect("role_list")

    return render(
        request,
        "students/edit_role.html",
        {
            "role": role,
        },
    )

@login_required
@admin_or_bursar
def delete_role(request, role_id):

    role = get_object_or_404(
        Group,
        id=role_id,
    )

    if request.method == "POST":

        role.delete()

        messages.success(
            request,
            "Role deleted successfully.",
        )

        return redirect("role_list")

    return render(
        request,
        "students/delete_role.html",
        {
            "role": role,
        },
    )

@login_required
@admin_or_bursar
def backup_database(request):

    database = settings.DATABASES["default"]["NAME"]

    backup_dir = os.path.join(
        settings.BASE_DIR,
        "backups",
    )

    os.makedirs(
        backup_dir,
        exist_ok=True,
    )

    backup_name = (
        f"school_backup_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
    )

    backup_path = os.path.join(
        backup_dir,
        backup_name,
    )

    shutil.copy2(
        database,
        backup_path,
    )

    messages.success(
        request,
        f"Database backed up successfully as {backup_name}.",
    )

    return redirect("settings")

@login_required
@admin_or_bursar
def restore_database(request):

    backup_dir = os.path.join(
        settings.BASE_DIR,
        "backups",
    )

    backups = []

    if os.path.exists(backup_dir):

        backups = sorted(
            os.listdir(backup_dir),
            reverse=True,
        )

    if request.method == "POST":

        backup_file = request.POST["backup_file"]

        source = os.path.join(
            backup_dir,
            backup_file,
        )

        destination = settings.DATABASES["default"]["NAME"]

        shutil.copy2(
            source,
            destination,
        )

        messages.success(
            request,
            "Database restored successfully.",
        )

        return redirect("settings")

    return render(
        request,
        "students/restore_database.html",
        {
            "backups": backups,
        },
    )

@login_required
@admin_or_bursar
def system_logs(request):

    logs = (
        LogEntry.objects
        .select_related(
            "user",
            "content_type",
        )
        .order_by("-action_time")
    )

    return render(
        request,
        "students/system_logs.html",
        {
            "logs": logs,
        },
    )


def register_school(request):

    # Only the system superuser can register a new school
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the system administrator can register a new school."
        )
        return redirect("home")

    if request.method == "POST":

        # -----------------------------
        # -----------------------------
        # SCHOOL INFORMATION
        # -----------------------------
        school_name = request.POST.get("school_name", "").strip()
        motto = request.POST.get("motto", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        website = request.POST.get("website", "").strip()
        current_term = request.POST.get("current_term", "").strip()
        academic_year = request.POST.get("academic_year", "").strip()
        # ADMINISTRATOR INFORMATION
        # -----------------------------
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        admin_email = request.POST.get("admin_email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # -----------------------------
        # BASIC VALIDATION
        # -----------------------------
        if not school_name:
            messages.error(request, "School name is required.")
            return redirect("register_school")

        if not first_name or not last_name:
            messages.error(
                request,
                "Administrator first and last name are required."
            )
            return redirect("register_school")

        if not username:
            messages.error(
                request,
                "Administrator username is required."
            )
            return redirect("register_school")

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "That username already exists."
            )
            return redirect("register_school")

        if not password:
            messages.error(
                request,
                "Administrator password is required."
            )
            return redirect("register_school")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return redirect("register_school")

        # -----------------------------
        # CREATE SCHOOL
        # -----------------------------
        school = SchoolProfile.objects.create(
            name=school_name,
            motto=motto,
            address=address,
            phone=phone,
            email=email,
            website=website,
            current_term=current_term,
            academic_year=academic_year,
        )

        # -----------------------------
        # CREATE ADMIN USER
        # -----------------------------
        user = User.objects.create_user(
            username=username,
            email=admin_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # -----------------------------
        # ADD ADMINISTRATOR ROLE
        # -----------------------------
        administrators_group, created = Group.objects.get_or_create(
            name="Administrators"
        )

        user.groups.add(administrators_group)

        # -----------------------------
        # CONNECT USER TO SCHOOL
        # -----------------------------
        SchoolUser.objects.create(
            user=user,
            school=school,
        )

        messages.success(
            request,
            f"{school.name} has been registered successfully. "
            f"Administrator account '{username}' was created."
        )

        return redirect("home")

    return render(
        request,
        "students/register_school.html",
    )
