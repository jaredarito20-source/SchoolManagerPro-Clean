from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.http import HttpResponse

from django.db.models import Count, Sum

from django.contrib.auth import get_user_model

from students.utils import get_user_school

from students.models import Student

User = get_user_model()



import os

from students.services.fee_ledger import (

    record_academic_year_opening_balances,

)

from students.services.enrollment import (

    create_next_period_enrollments,

)

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

    Teacher,

)

from students.services.fee_ledger import (

    record_academic_year_opening_balances,

)

from students.services.enrollment import (

    create_next_period_enrollments,

)



@login_required

@in_group("Administrators")

def assign_student_parent(request):



    school = get_user_school(request.user)



    if not school:

        messages.error(

            request,

            "Your account is not associated with a school."

        )

        return redirect("students:home")



    # Only parent accounts belonging to this school

    parent_users = User.objects.filter(

        school_user__school=school,

        groups__name="Parents",

    ).distinct().order_by("username")



    # Only students belonging to this school

    students = Student.objects.filter(

        school=school

    ).select_related(

        "school_class",

        "parent_user",

    ).order_by(

        "admission_number"

    )



    if request.method == "POST":



        parent_id = request.POST.get("parent")

        student_id = request.POST.get("student")



        if not parent_id or not student_id:

            messages.error(

                request,

                "Please select both a parent and a student."

            )

            return redirect("students:assign_student_parent")



        # Make sure parent belongs to this school

        parent = get_object_or_404(

            User,

            id=parent_id,

            school_user__school=school,

            groups__name="Parents",

        )



        # Make sure student belongs to this school

        student = get_object_or_404(

            Student,

            id=student_id,

            school=school,

        )



        student.parent_user = parent

        student.save(update_fields=["parent_user"])



        messages.success(

            request,

            f"{student.first_name} {student.last_name} "

            f"has been assigned to parent account "

            f"{parent.username}."

        )



        return redirect("students:assign_student_parent")



    return render(

        request,

        "students/assign_student_parent.html",

        {

            "parent_users": parent_users,

            "students": students,

        },

    )







@login_required

@in_group(

    "Administrators",

    "Head Teacher",

)

def admin_reset_user_password(request, id):



    user = get_object_or_404(

        User,

        id=id,

    )



    # -----------------------------------------

    # PREVENT RESETTING SUPERUSER

    # -----------------------------------------



    if user.is_superuser:



        messages.error(

            request,

            "You cannot reset the password of a superuser."

        )



        return redirect("students:user_list")



    # -----------------------------------------

    # SCHOOL SECURITY

    # -----------------------------------------



    if not request.user.is_superuser:



        admin_school_user = getattr(

            request.user,

            "school_user",

            None,

        )



        target_school_user = getattr(

            user,

            "school_user",

            None,

        )



        if not admin_school_user:



            messages.error(

                request,

                "Your account is not linked to a school."

            )



            return redirect("students:home")



        if not target_school_user:



            messages.error(

                request,

                "The selected user is not linked to a school."

            )



            return redirect("students:user_list")



        if (

            admin_school_user.school_id

            != target_school_user.school_id

        ):



            messages.error(

                request,

                "You cannot reset a user from another school."

            )



            return redirect("students:user_list")



    # -----------------------------------------

    # RESET PASSWORD

    # -----------------------------------------



    if request.method == "POST":



        password = request.POST.get(

            "password"

        )



        password_confirm = request.POST.get(

            "password_confirm"

        )



        if not password:



            messages.error(

                request,

                "Please enter a new password."

            )



            return redirect(

                "admin_reset_user_password",

                id=user.id,

            )



        if password != password_confirm:



            messages.error(

                request,

                "The passwords do not match."

            )



            return redirect(

                "admin_reset_user_password",

                id=user.id,

            )



        if len(password) < 8:



            messages.error(

                request,

                "Password must contain at least 8 characters."

            )



            return redirect(

                "admin_reset_user_password",

                id=user.id,

            )



        user.set_password(password)



        user.save()



        messages.success(

            request,

            f"Password reset successfully for {user.username}."

        )



        return redirect("students:user_list")



    return render(

        request,

        "registration/admin_reset_user_password.html",

        {

            "target_user": user,

        },

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



    school = None



    # Administrator

    if (

        user.is_superuser

        or user.groups.filter(

            name="Administrators"

        ).exists()

    ):

        role = "administrator"



        # Administrator school

        if hasattr(user, "school_user"):

            school = user.school_user.school



    # Teacher

    elif user.groups.filter(

        name="Teachers"

    ).exists():



        role = "teacher"



        teacher = Teacher.objects.filter(

            user=user

        ).select_related(

            "school"

        ).first()



        if teacher:

            school = teacher.school



    # Bursar

    elif user.groups.filter(

        name="Bursar"

    ).exists():



        role = "bursar"



        if hasattr(user, "school_user"):

            school = user.school_user.school



    # Parent

    elif user.groups.filter(

        name="Parents"

    ).exists():



        return redirect("parent_dashboard")



    # Head Teacher

    elif user.groups.filter(

        name="Head Teacher"

    ).exists():



        role = "head_teacher"



        if hasattr(user, "school_user"):

            school = user.school_user.school



    # Secretary

    elif user.groups.filter(

        name="Secretaries"

    ).exists():



        role = "secretary"



        if hasattr(user, "school_user"):

            school = user.school_user.school



    else:

        role = "user"



    return render(

        request,

        "students/home.html",

        {

            "role": role,

            "school": school,

        }

    )

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

def edit_school_profile(request, id):



    # -----------------------------------

    # SYSTEM SUPERUSER ONLY

    # -----------------------------------



    if not request.user.is_superuser:

        messages.error(

            request,

            "Only the system administrator can edit school profiles."

        )

        return redirect("students:home")



    # -----------------------------------

    # GET THE SELECTED SCHOOL

    # -----------------------------------



    try:

        profile = SchoolProfile.objects.get(id=id)

    except SchoolProfile.DoesNotExist:

        messages.error(

            request,

            "School not found."

        )

        return redirect("students:school_list")



    # -----------------------------------

    # SAVE CHANGES

    # -----------------------------------



    if request.method == "POST":



        old_academic_year = str(

            profile.academic_year

        ).strip()



        old_current_term = str(

            profile.current_term

        ).strip()



        new_academic_year = request.POST.get(

            "academic_year",

            ""

        ).strip()



        new_current_term = request.POST.get(

            "current_term",

            ""

        ).strip()

        new_curriculum_system = request.POST.get(
            "curriculum_system",
            ""
        ).strip()

        valid_curriculum_systems = {
            "CBC",
            "8-4-4",
            "BOTH",
        }

        if new_curriculum_system not in valid_curriculum_systems:
            messages.error(
                request,
                "Please select a valid curriculum system.",
            )
            return redirect(
                "students:edit_school_profile",
                id=id,
            )



        profile.name = request.POST.get("name", "").strip()

        profile.motto = request.POST.get("motto", "").strip()

        profile.address = request.POST.get("address", "").strip()

        profile.phone = request.POST.get("phone", "").strip()

        profile.email = request.POST.get("email", "").strip()

        profile.website = request.POST.get("website", "").strip()



        profile.academic_year = new_academic_year

        profile.current_term = new_current_term



        profile.principal_name = request.POST.get(

            "principal_name",

            ""

        ).strip()

        if request.FILES.get("logo"):

            profile.logo = request.FILES["logo"]



        if request.FILES.get("principal_signature"):

            profile.principal_signature = request.FILES[

                "principal_signature"

            ]



        if request.FILES.get("school_stamp"):

            profile.school_stamp = request.FILES[

                "school_stamp"

            ]



        # -----------------------------------

        # CREATE NEXT ACADEMIC ENROLLMENTS

        # -----------------------------------



        if (

            old_academic_year

            and old_current_term

            and new_academic_year

            and new_current_term

            and (

                old_academic_year != new_academic_year

                or old_current_term != new_current_term

            )

        ):

            try:

                create_next_period_enrollments(

                    school=profile,

                    old_academic_year=old_academic_year,

                    old_term=old_current_term,

                    new_academic_year=new_academic_year,

                    new_term=new_current_term,

                )

            except ValueError as exc:

                messages.error(

                    request,

                    str(exc),

                )

                return redirect(

                    "edit_school_profile",

                    id=id,

                )



        # -----------------------------------

        # ACADEMIC YEAR FINANCE ROLLOVER

        # -----------------------------------



        if (

            old_academic_year

            and new_academic_year

            and old_academic_year != new_academic_year

        ):

            record_academic_year_opening_balances(

                school=profile,

                new_academic_year=new_academic_year,

                recorded_by=request.user,

            )



        profile.save()



        messages.success(

            request,

            f"{profile.name} school profile updated successfully."

        )



        return redirect("students:school_list")



    # -----------------------------------

    # DISPLAY EDIT PAGE

    # -----------------------------------



    return render(

        request,

        "students/edit_school_profile.html",

        {

            "profile": profile,

        },

    )





@login_required

def delete_school(request, id):

    if not request.user.is_superuser:

        messages.error(

            request,

            "Only the system superuser can delete a school."

        )

        return redirect("students:school_list")



    school = get_object_or_404(

        SchoolProfile,

        id=id

    )



    if request.method == "POST":

        school_name = school.name



        school.delete()



        messages.success(

            request,

            f"School '{school_name}' was deleted successfully."

        )



        return redirect("students:school_list")



    return render(

        request,

        "students/delete_school.html",

        {

            "school": school,

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



        profile.name = request.POST.get("school_name")

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



    # -----------------------------------

    # SYSTEM SUPERUSER

    # -----------------------------------



    if request.user.is_superuser:



        users = (

            User.objects

            .filter(

                school_user__isnull=False

            )

            .select_related(

                "school_user__school"

            )

            .prefetch_related(

                "groups"

            )

            .order_by(

                "school_user__school__name",

                "username",

            )

        )



    # -----------------------------------

    # SCHOOL USER

    # -----------------------------------



    else:



        school = get_user_school(request.user)



        if not school:

            messages.error(

                request,

                "Your account is not associated with a school."

            )

            return redirect("students:home")



        users = (

            User.objects

            .filter(

                school_user__school=school

            )

            .prefetch_related(

                "groups"

            )

            .order_by(

                "username"

            )

        )



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



    school = get_user_school(request.user)



    if not school:

        messages.error(

            request,

            "Your account is not associated with a school."

        )

        return redirect("students:home")



    groups = Group.objects.all().order_by("name")



    subjects = Subject.objects.filter(

        school=school

    ).select_related(

        "school_class"

    ).order_by(

        "school_class__name",

        "name",

    )



    if request.method == "POST":



        username = request.POST.get("username", "").strip()

        first_name = request.POST.get("first_name", "").strip()

        last_name = request.POST.get("last_name", "").strip()

        email = request.POST.get("email", "").strip()

        password = request.POST.get("password", "")

        group_name = request.POST.get("group", "")



        assigned_subject_ids = request.POST.getlist(

            "assigned_subjects"

        )



        employee_number = request.POST.get(

            "employee_number", ""

        ).strip()



        gender = request.POST.get(

            "gender", ""

        ).strip()



        phone = request.POST.get(

            "phone", ""

        ).strip()



        # -----------------------------

        # VALIDATION

        # -----------------------------



        if not username:

            messages.error(

                request,

                "Username is required."

            )



            return render(

                request,

                "students/add_user.html",

                {

                    "groups": groups,

                },

            )



        if not password:

            messages.error(

                request,

                "Password is required."

            )



            return render(

                request,

                "students/add_user.html",

                {

                    "groups": groups,

                },

            )



        if not first_name or not last_name:

            messages.error(

                request,

                "First name and last name are required."

            )



            return render(

                request,

                "students/add_user.html",

                {

                    "groups": groups,

                },

            )



        if User.objects.filter(

            username=username

        ).exists():



            messages.error(

                request,

                "Username already exists."

            )



            return render(

                request,

                "students/add_user.html",

                {

                    "groups": groups,

                },

            )



        # -----------------------------

        # TEACHER VALIDATION

        # -----------------------------



        if group_name == "Teachers":



            if not employee_number:

                messages.error(

                    request,

                    "Employee number is required for teachers."

                )



                return render(

                    request,

                    "students/add_user.html",

                    {

                        "groups": groups,

                    },

                )



            if not gender:

                messages.error(

                    request,

                    "Gender is required for teachers."

                )



                return render(

                    request,

                    "students/add_user.html",

                    {

                        "groups": groups,

                    },

                )



            if not phone:

                messages.error(

                    request,

                    "Phone number is required for teachers."

                )



                return render(

                    request,

                    "students/add_user.html",

                    {

                        "groups": groups,

                    },

                )



            if Teacher.objects.filter(

                employee_number=employee_number

            ).exists():



                messages.error(

                    request,

                    "Employee number already exists."

                )



                return render(

                    request,

                    "students/add_user.html",

                    {

                        "groups": groups,

                    },

                )



        # -----------------------------

        # CREATE USER

        # -----------------------------



        user = User.objects.create_user(

            username=username,

            email=email,

            password=password,

            first_name=first_name,

            last_name=last_name,

        )



        # -----------------------------

        # ASSIGN GROUP

        # -----------------------------



        if group_name:



            group = get_object_or_404(

                Group,

                name=group_name,

            )



            user.groups.add(group)



        # -----------------------------

        # CREATE SCHOOL USER

        # -----------------------------



        SchoolUser.objects.create(

            user=user,

            school=school,

        )



        # -----------------------------

        # CREATE TEACHER PROFILE

        # -----------------------------



        if group_name == "Teachers":



            teacher = Teacher.objects.create(

                user=user,

                school=school,

                employee_number=employee_number,

                first_name=first_name,

                last_name=last_name,

                gender=gender,

                phone=phone,

                email=email,

            )



            Subject.objects.filter(

                id__in=assigned_subject_ids,

                school=school,

            ).update(

                teacher=teacher

            )



        messages.success(

            request,

            "User created successfully."

        )



        return redirect("students:user_list")



    return render(

        request,

        "students/add_user.html",

        {

            "groups": groups,

            "subjects": subjects,

        },

    )

@login_required

@admin_or_bursar

def edit_user(request, user_id):



    user = get_object_or_404(

        User,

        id=user_id,

    )



    # -----------------------------------

    # Determine user's school

    # -----------------------------------



    school_user = SchoolUser.objects.filter(

        user=user

    ).select_related(

        "school"

    ).first()



    school = school_user.school if school_user else None



    # -----------------------------------

    # Groups

    # -----------------------------------



    groups = Group.objects.all().order_by("name")



    # -----------------------------------

    # Teacher profile

    # -----------------------------------



    teacher = Teacher.objects.filter(

        user=user

    ).first()



    # -----------------------------------

    # Subjects available for this school

    # -----------------------------------



    subjects = Subject.objects.none()



    if school:



        subjects = Subject.objects.filter(

            school=school

        ).select_related(

            "school_class"

        ).order_by(

            "school_class__name",

            "name",

        )



    if request.method == "POST":



        # --------------------------------

        # Basic user fields

        # --------------------------------



        username = request.POST.get(

            "username",

            ""

        ).strip()



        first_name = request.POST.get(

            "first_name",

            ""

        ).strip()



        last_name = request.POST.get(

            "last_name",

            ""

        ).strip()



        email = request.POST.get(

            "email",

            ""

        ).strip()



        password = request.POST.get(

            "password",

            ""

        )



        group_name = request.POST.get(

            "group",

            ""

        )



        assigned_subject_ids = request.POST.getlist(

            "assigned_subjects"

        )



        # --------------------------------

        # Update basic user information

        # --------------------------------



        user.username = username

        user.first_name = first_name

        user.last_name = last_name

        user.email = email



        if password:

            user.set_password(password)



        user.save()



        # --------------------------------

        # Update group

        # --------------------------------



        user.groups.clear()



        if group_name:



            group = get_object_or_404(

                Group,

                name=group_name,

            )



            user.groups.add(group)



        # --------------------------------

        # Teacher information

        # --------------------------------



        if group_name == "Teachers":



            employee_number = request.POST.get(

                "employee_number",

                ""

            ).strip()



            gender = request.POST.get(

                "gender",

                ""

            ).strip()



            phone = request.POST.get(

                "phone",

                ""

            ).strip()



            # --------------------------------

            # Create teacher profile if missing

            # --------------------------------



            if not teacher:



                if not school:

                    messages.error(

                        request,

                        "User is not associated with a school."

                    )

                    return redirect(

                        "edit_user",

                        user_id=user.id,

                    )



                teacher = Teacher.objects.create(

                    user=user,

                    school=school,

                    employee_number=employee_number,

                    first_name=first_name,

                    last_name=last_name,

                    gender=gender,

                    phone=phone,

                    email=email,

                )



            else:



                teacher.employee_number = employee_number

                teacher.first_name = first_name

                teacher.last_name = last_name

                teacher.gender = gender

                teacher.phone = phone

                teacher.email = email



                teacher.save()



            # --------------------------------

            # Update assigned subjects

            # --------------------------------



            if school:



                Subject.objects.filter(

                    teacher=teacher,

                    school=school,

                ).update(

                    teacher=None

                )



                Subject.objects.filter(

                    id__in=assigned_subject_ids,

                    school=school,

                ).update(

                    teacher=teacher

                )



        else:



            # --------------------------------

            # User is no longer a teacher

            # --------------------------------



            if teacher:



                Subject.objects.filter(

                    teacher=teacher

                ).update(

                    teacher=None

                )



                teacher.delete()



        messages.success(

            request,

            "User updated successfully.",

        )



        return redirect("students:user_list")



    # -----------------------------------

    # Current assigned subjects

    # -----------------------------------



    assigned_subjects = Subject.objects.none()



    if teacher:



        assigned_subjects = Subject.objects.filter(

            teacher=teacher

        ).values_list(

            "id",

            flat=True

        )



    return render(

        request,

        "students/edit_user.html",

        {

            "user_obj": user,

            "groups": groups,

            "teacher": teacher,

            "subjects": subjects,

            "assigned_subjects": assigned_subjects,

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



        return redirect("students:user_list")



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

        return redirect("students:home")



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



        return redirect("students:home")



    return render(

        request,

        "students/register_school.html",

    )

@login_required

@in_group("Administrators", "Head Teacher")

def reset_user_password(request, id):



    user = get_object_or_404(User, id=id)



    if request.method == "POST":



        password = request.POST.get("password")

        confirm_password = request.POST.get("confirm_password")



        if not password:

            messages.error(

                request,

                "Please enter a new password."

            )

            return redirect(

                "reset_user_password",

                id=user.id,

            )



        if password != confirm_password:

            messages.error(

                request,

                "Passwords do not match."

            )

            return redirect(

                "reset_user_password",

                id=user.id,

            )



        user.set_password(password)

        user.save()



        messages.success(

            request,

            f"Password for {user.username} has been reset successfully."

        )



        return redirect("students:user_list")



    return render(

        request,

        "students/reset_user_password.html",

        {

            "user_account": user,

        },

    )

@login_required
@admin_or_bursar
def cbc_teacher_assignment_list(request):

    # -------------------------------------------------
    # SCHOOL
    # -------------------------------------------------

    if request.user.is_superuser:
        school_id = request.GET.get("school")

        if school_id:
            assignments = TeacherAssessmentAssignment.objects.filter(
                school_class_curriculum__school_class__school_id=school_id
            )
        else:
            assignments = TeacherAssessmentAssignment.objects.all()

        schools = SchoolProfile.objects.all().order_by("name")

    else:
        school = get_user_school(request.user)

        if not school:
            return HttpResponseForbidden(
                "Your account is not associated with a school."
            )

        assignments = TeacherAssessmentAssignment.objects.filter(
            school_class_curriculum__school_class__school=school
        )

        schools = SchoolProfile.objects.filter(
            id=school.id
        )

    # -------------------------------------------------
    # OPTIONAL FILTERS
    # -------------------------------------------------

    academic_year = request.GET.get(
        "academic_year",
        ""
    ).strip()

    term = request.GET.get(
        "term",
        ""
    ).strip()

    class_id = request.GET.get(
        "class_id",
        ""
    ).strip()

    if academic_year:
        assignments = assignments.filter(
            academic_year=academic_year
        )

    if term:
        assignments = assignments.filter(
            term=term
        )

    if class_id:
        assignments = assignments.filter(
            school_class_curriculum__school_class_id=class_id
        )

    assignments = assignments.select_related(
        "teacher",
        "teacher__user",
        "school_class_curriculum",
        "school_class_curriculum__school_class",
        "school_class_curriculum__curriculum_grade",
        "school_class_curriculum__pathway",
        "learning_area",
        "learning_area__curriculum_grade",
        "learning_area__pathway",
    ).order_by(
        "-academic_year",
        "term",
        "school_class_curriculum__school_class__name",
        "learning_area__name",
        "teacher__user__first_name",
        "teacher__user__last_name",
    )

    # -------------------------------------------------
    # CLASSES FOR FILTER
    # -------------------------------------------------

    if request.user.is_superuser:
        classes = SchoolClass.objects.all()
    else:
        classes = SchoolClass.objects.filter(
            school=get_user_school(request.user)
        )

    classes = classes.filter(
        curriculum="CBC"
    ).order_by("name")

    return render(
        request,
        "students/cbc_teacher_assignment_list.html",
        {
            "assignments": assignments,
            "schools": schools,
            "classes": classes,
            "selected_school": request.GET.get("school", ""),
            "selected_year": academic_year,
            "selected_term": term,
            "selected_class": class_id,
        },
    )
@login_required
@admin_or_bursar
def cbc_teacher_assignment_add(request):

    # -------------------------------------------------
    # GET CURRENT SCHOOL
    # -------------------------------------------------

    if request.user.is_superuser:

        school_id = request.GET.get("school")

        if school_id:
            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )
        else:
            school = None

    else:

        school = get_user_school(request.user)

        if not school:
            return HttpResponseForbidden(
                "Your account is not associated with a school."
            )

    # -------------------------------------------------
    # AVAILABLE CLASSES
    # -------------------------------------------------

    if school:

        class_curricula = (
            SchoolClassCurriculum.objects
            .select_related(
                "school_class",
                "curriculum_grade",
                "pathway",
                "curriculum_version",
            )
            .filter(
                school_class__school=school,
                school_class__curriculum="CBC",
            )
            .order_by(
                "school_class__name",
                "-academic_year",
            )
        )

    else:

        class_curricula = (
            SchoolClassCurriculum.objects
            .select_related(
                "school_class",
                "curriculum_grade",
                "pathway",
                "curriculum_version",
            )
            .filter(
                school_class__curriculum="CBC"
            )
            .order_by(
                "school_class__name",
                "-academic_year",
            )
        )

    # -------------------------------------------------
    # POST
    # -------------------------------------------------

    if request.method == "POST":

        class_curriculum_id = request.POST.get(
            "school_class_curriculum"
        )

        teacher_id = request.POST.get(
            "teacher"
        )

        learning_area_id = request.POST.get(
            "learning_area"
        )

        term = request.POST.get(
            "term"
        )

        # ---------------------------------------------
        # REQUIRED FIELDS
        # ---------------------------------------------

        if not class_curriculum_id:
            messages.error(
                request,
                "Please select a CBC class.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        if not teacher_id:
            messages.error(
                request,
                "Please select a teacher.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        if not learning_area_id:
            messages.error(
                request,
                "Please select a learning area.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        if term not in {"1", "2", "3"}:
            messages.error(
                request,
                "Please select a valid term.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        # ---------------------------------------------
        # GET CLASS CURRICULUM
        # ---------------------------------------------

        if school:

            class_curriculum = get_object_or_404(
                SchoolClassCurriculum,
                id=class_curriculum_id,
                school_class__school=school,
                school_class__curriculum="CBC",
            )

        else:

            class_curriculum = get_object_or_404(
                SchoolClassCurriculum,
                id=class_curriculum_id,
                school_class__curriculum="CBC",
            )

        # ---------------------------------------------
        # GET TEACHER
        # ---------------------------------------------

        teacher = get_object_or_404(
            Teacher,
            id=teacher_id,
        )

        # ---------------------------------------------
        # SCHOOL SECURITY
        # ---------------------------------------------

        if (
            teacher.school_id
            != class_curriculum.school_class.school_id
        ):
            messages.error(
                request,
                "The teacher must belong to the same school as the CBC class.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        # ---------------------------------------------
        # GET LEARNING AREA
        # ---------------------------------------------

        learning_area = get_object_or_404(
            CurriculumLearningArea.objects.select_related(
                "curriculum_grade",
                "pathway",
            ),
            id=learning_area_id,
        )

        curriculum_grade = (
            class_curriculum.curriculum_grade
        )

        # ---------------------------------------------
        # GRADE VALIDATION
        # ---------------------------------------------

        if (
            learning_area.curriculum_grade_id
            != curriculum_grade.id
        ):
            messages.error(
                request,
                "The learning area does not belong to this class grade.",
            )
            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        # ---------------------------------------------
        # PATHWAY VALIDATION
        # ---------------------------------------------

        senior_grades = {
            "GRADE10",
            "GRADE11",
            "GRADE12",
        }

        if curriculum_grade.grade in senior_grades:

            if not class_curriculum.pathway:
                messages.error(
                    request,
                    "Grade 10-12 CBC classes must have a pathway configured.",
                )
                return redirect(
                    "students:cbc_teacher_assignment_add"
                )

            if (
                learning_area.pathway_id
                != class_curriculum.pathway_id
            ):
                messages.error(
                    request,
                    "The learning area does not belong to this class pathway.",
                )
                return redirect(
                    "students:cbc_teacher_assignment_add"
                )

        else:

            if learning_area.pathway_id:
                messages.error(
                    request,
                    "PP1-Grade 9 learning areas cannot have a pathway.",
                )
                return redirect(
                    "students:cbc_teacher_assignment_add"
                )

        # ---------------------------------------------
        # ACADEMIC YEAR
        # ---------------------------------------------

        academic_year = (
            class_curriculum.academic_year
        )

        # ---------------------------------------------
        # PREVENT DUPLICATE ASSIGNMENT
        # ---------------------------------------------

        if TeacherAssessmentAssignment.objects.filter(
            teacher=teacher,
            school_class_curriculum=class_curriculum,
            learning_area=learning_area,
            academic_year=academic_year,
            term=term,
        ).exists():

            messages.error(
                request,
                "This teacher is already assigned to this learning area, class and term.",
            )

            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        # ---------------------------------------------
        # CREATE ASSIGNMENT
        # ---------------------------------------------

        assignment = TeacherAssessmentAssignment(
            teacher=teacher,
            school_class_curriculum=class_curriculum,
            learning_area=learning_area,
            academic_year=academic_year,
            term=term,
        )

        try:

            assignment.full_clean()
            assignment.save()

        except Exception as exc:

            messages.error(
                request,
                f"Unable to create assignment: {exc}",
            )

            return redirect(
                "students:cbc_teacher_assignment_add"
            )

        messages.success(
            request,
            "CBC teacher assignment created successfully.",
        )

        return redirect(
            "students:cbc_teacher_assignment_list"
        )

    # -------------------------------------------------
    # GET FORM DATA
    # -------------------------------------------------

    teachers = Teacher.objects.all()

    learning_areas = CurriculumLearningArea.objects.all()

    if school:

        teachers = teachers.filter(
            school=school
        )

        learning_areas = learning_areas.filter(
            curriculum_grade__curriculum_version__in=CurriculumVersion.objects.all()
        )

    teachers = teachers.select_related(
        "user",
        "school",
    ).order_by(
        "user__first_name",
        "user__last_name",
        "user__username",
    )

    learning_areas = learning_areas.select_related(
        "curriculum_grade",
        "pathway",
    ).order_by(
        "curriculum_grade__grade",
        "pathway__name",
        "name",
    )

    schools = SchoolProfile.objects.all().order_by(
        "name"
    )

    return render(
        request,
        "students/cbc_teacher_assignment_form.html",
        {
            "school": school,
            "schools": schools,
            "class_curricula": class_curricula,
            "teachers": teachers,
            "learning_areas": learning_areas,
        },
    )







