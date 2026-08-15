from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from io import BytesIO
from django.db.models import Count
from students.utils import get_user_school
from students.models import SchoolClass, SchoolProfile, Teacher,Student
from datetime import date
from django.http import JsonResponse, FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from students.models import (
    SchoolProfile,
    SchoolClass,
    SchoolUser,
    Exam,
    ExamTimetable,
    Subject,
    Teacher,
)


from django.contrib.auth.models import User, Group



from django.db.models import Avg
from students.decorators import (
    admin_or_bursar,
    admin_or_teacher,
    admin_teacher_secretary,
    in_group,
    admin_required,
)

from students.decorators import (
    admin_or_bursar,
    in_group,
)

from students.models import *




@login_required
@admin_required
def add_teacher(request):

    if request.method == "POST":

        employee_number = request.POST["employee_number"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        gender = request.POST["gender"]
        phone = request.POST["phone"]
        email = request.POST["email"]

        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        # Check passwords
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("add_teacher")

        # Check username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("add_teacher")

        # Check employee number
        if Teacher.objects.filter(employee_number=employee_number).exists():
            messages.error(request, "Employee number already exists.")
            return redirect("add_teacher")

        # Create login account
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # Add user to Teachers group
        teacher_group, created = Group.objects.get_or_create(name="Teachers")
        user.groups.add(teacher_group)

        # Create Teacher profile
        Teacher.objects.create(
            user=user,
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            phone=phone,
            email=email,
        )

        messages.success(
            request,
            f"Teacher '{first_name} {last_name}' created successfully."
        )

        return redirect("teacher_list")

    return render(
        request,
        "teachers/add_teacher.html",
    )



@login_required
@admin_or_bursar
def add_student(request):

    # -----------------------------------
    # Determine available schools/classes
    # -----------------------------------

    if request.user.is_superuser:
        schools = SchoolProfile.objects.all().order_by("name")
        classes = SchoolClass.objects.select_related(
            "school"
        ).order_by("school__name", "name")

    else:
        school = request.user.school_user.school

        schools = [school]

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by("name")

    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == "POST":

        admission_number = request.POST.get(
            "admission_number", ""
        ).strip()

        first_name = request.POST.get(
            "first_name", ""
        ).strip()

        last_name = request.POST.get(
            "last_name", ""
        ).strip()

        gender = request.POST.get("gender")

        date_of_birth = request.POST.get(
            "date_of_birth"
        )

        school_class_id = request.POST.get(
            "school_class"
        )

        parent_name = request.POST.get(
            "parent_name", ""
        ).strip()

        phone = request.POST.get(
            "phone", ""
        ).strip()

        # -----------------------------------
        # Determine school
        # -----------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get("school")

            if not school_id:
                messages.error(
                    request,
                    "Please select a school."
                )
                return redirect("add_student")

            school = SchoolProfile.objects.filter(
                id=school_id
            ).first()

            if not school:
                messages.error(
                    request,
                    "Invalid school."
                )
                return redirect("add_student")

        else:

            # Normal school users can NEVER
            # choose another school.
            school = request.user.school_user.school

        # -----------------------------------
        # Validate class belongs to school
        # -----------------------------------

        school_class = SchoolClass.objects.filter(
            id=school_class_id,
            school=school,
        ).first()

        if not school_class:
            messages.error(
                request,
                "Invalid class selected for this school."
            )
            return redirect("add_student")

        # -----------------------------------
        # Prevent duplicate admission number
        # within the same school
        # -----------------------------------

        if Student.objects.filter(
            school=school,
            admission_number=admission_number,
        ).exists():

            messages.error(
                request,
                f"Admission number {admission_number} "
                f"already exists in {school.name}."
            )

            return redirect("add_student")

        # -----------------------------------
        # Create student
        # -----------------------------------

        Student.objects.create(
            admission_number=admission_number,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            school=school,
            school_class=school_class,
            parent_name=parent_name,
            phone=phone,
        )

        messages.success(
            request,
            f"{first_name} {last_name} has been "
            f"added successfully."
        )

        return redirect("student_list")

    # -----------------------------------
    # GET
    # -----------------------------------

    return render(
        request,
        "students/add_student.html",
        {
            "schools": schools,
            "classes": classes,
        },
    )

@login_required
@admin_or_bursar
def student_list(request):

    if request.user.is_superuser:

        students = Student.objects.select_related(
            "school",
            "school_class",
        ).all().order_by(
            "school__name",
            "school_class__name",
            "first_name",
        )

    else:

        school = request.user.school_user.school

        students = Student.objects.select_related(
            "school",
            "school_class",
        ).filter(
            school=school
        ).order_by(
            "school_class__name",
            "first_name",
        )

    return render(
        request,
        "students/student_list.html",
        {
            "students": students,
        },
    )

@login_required
def edit_student(request, id):

    if request.user.is_superuser:

        student = get_object_or_404(
            Student,
            id=id
        )

        schools = SchoolProfile.objects.all()

        classes = SchoolClass.objects.select_related(
            "school"
        ).all().order_by("name")

        parents = User.objects.filter(
            groups__name="Parents"
        ).order_by("username")

    else:

        school = request.user.school_user.school

        student = get_object_or_404(
            Student,
            id=id,
            school=school
        )

        schools = [school]

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by("name")

        parents = User.objects.filter(
            groups__name="Parents"
        ).order_by("username")

    if request.method == "POST":

        student.admission_number = request.POST.get(
            "admission_number"
        )
        student.first_name = request.POST.get(
            "first_name"
        )
        student.last_name = request.POST.get(
            "last_name"
        )
        student.gender = request.POST.get(
            "gender"
        )
        student.date_of_birth = request.POST.get(
            "date_of_birth"
        )

        class_id = request.POST.get("school_class")

        if class_id:
            student.school_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=student.school,
            )
        else:
            student.school_class = None

        student.parent_name = request.POST.get(
            "parent_name"
        )
        student.phone = request.POST.get(
            "phone"
        )

        parent_user_id = request.POST.get(
            "parent_user"
        )

        if parent_user_id:
            student.parent_user = get_object_or_404(
                User,
                id=parent_user_id,
                groups__name="Parents",
            )
        else:
            student.parent_user = None

        if request.FILES.get("photo"):
            student.photo = request.FILES["photo"]

        student.save()

        messages.success(
            request,
            "Student updated successfully."
        )

        return redirect("student_list")

    return render(
        request,
        "students/edit_student.html",
        {
            "student": student,
            "schools": schools,
            "classes": classes,
            "parents": parents,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def promotion_list(request):

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

        # ======================================
        # ONLY THIS SCHOOL'S CLASSES
        # ======================================

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "students/promotion_list.html",
        {
            "classes": classes,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def promote_students(request):

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # ==========================================
    # PROMOTE STUDENTS
    # ==========================================

    if request.method == "POST":

        from_class_id = request.POST.get(
            "from_class"
        )

        to_class_id = request.POST.get(
            "to_class"
        )

        if not from_class_id or not to_class_id:

            messages.error(
                request,
                "Please select both the current class and the destination class."
            )

            return redirect(
                "promotion_list"
            )

        # ======================================
        # GET CLASSES SECURELY
        # ======================================

        if request.user.is_superuser:

            from_class = get_object_or_404(
                SchoolClass,
                id=from_class_id,
            )

            to_class = get_object_or_404(
                SchoolClass,
                id=to_class_id,
            )

        else:

            from_class = get_object_or_404(
                SchoolClass,
                id=from_class_id,
                school=school,
            )

            to_class = get_object_or_404(
                SchoolClass,
                id=to_class_id,
                school=school,
            )

        # ======================================
        # PREVENT SAME CLASS
        # ======================================

        if from_class.id == to_class.id:

            messages.error(
                request,
                "Students cannot be promoted to the same class."
            )

            return redirect(
                "promotion_list"
            )

        # ======================================
        # GET STUDENTS
        # ======================================

        if request.user.is_superuser:

            students = Student.objects.filter(
                school_class=from_class
            )

        else:

            students = Student.objects.filter(
                school=school,
                school_class=from_class,
            )

        # ======================================
        # PROMOTE
        # ======================================

        count = students.update(
            school_class=to_class
        )

        # ======================================
        # SUCCESS MESSAGE
        # ======================================

        messages.success(
            request,
            f"{count} students promoted from "
            f"{from_class.name} to {to_class.name}."
        )

        return redirect(
            "promotion_list"
        )

    return redirect(
        "promotion_list"
    )
@login_required
@admin_or_bursar
def delete_student(request, id):

    if request.user.is_superuser:
        student = get_object_or_404(
            Student,
            id=id
        )
    else:
        school = request.user.school_user.school

        student = get_object_or_404(
            Student,
            id=id,
            school=school
        )

    if request.method == "POST":
        student_name = f"{student.first_name} {student.last_name}"

        student.delete()

        messages.success(
            request,
            f"{student_name} has been deleted successfully."
        )

        return redirect("student_list")

    return render(
        request,
        "students/delete_student.html",
        {
            "student": student,
        },
    )

@login_required
@admin_or_bursar
def teacher_list(request):

    if request.user.is_superuser:
        teachers = Teacher.objects.select_related(
            "school"
        ).prefetch_related(
            "subjects",
            "subjects__school_class",
        ).all()

    else:
        school = request.user.school_user.school

        teachers = Teacher.objects.select_related(
            "school"
        ).prefetch_related(
            "subjects",
            "subjects__school_class",
        ).filter(
            school=school
        )

    return render(
        request,
        "students/teacher_list.html",
        {
            "teachers": teachers,
        },
    )
from django.contrib.auth.models import User, Group
from django.contrib import messages

@login_required
@admin_required
def add_teacher(request):

    # --------------------------------
    # AVAILABLE SCHOOLS
    # --------------------------------

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all()

    else:

        school = request.user.school_user.school

        schools = [school]

    # --------------------------------
    # POST
    # --------------------------------

    if request.method == "POST":

        employee_number = request.POST.get(
            "employee_number",
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

        gender = request.POST.get(
            "gender"
        )

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # --------------------------------
        # DETERMINE SCHOOL
        # --------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get(
                "school"
            )

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect(
                    "add_teacher"
                )

            school = SchoolProfile.objects.filter(
                id=school_id
            ).first()

            if not school:

                messages.error(
                    request,
                    "Invalid school selected."
                )

                return redirect(
                    "add_teacher"
                )

        else:

            school = request.user.school_user.school

        # --------------------------------
        # PASSWORD CHECK
        # --------------------------------

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect(
                "add_teacher"
            )

        # --------------------------------
        # USERNAME CHECK
        # --------------------------------

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect(
                "add_teacher"
            )

        # --------------------------------
        # EMPLOYEE NUMBER CHECK
        # --------------------------------

        if Teacher.objects.filter(
            employee_number=employee_number
        ).exists():

            messages.error(
                request,
                "Employee number already exists."
            )

            return redirect(
                "add_teacher"
            )

        # --------------------------------
        # CREATE USER
        # --------------------------------

        user = User.objects.create_user(

            username=username,
            password=password,

            first_name=first_name,
            last_name=last_name,
            email=email,

        )

        # --------------------------------
        # TEACHER GROUP
        # --------------------------------

        teacher_group = Group.objects.get(
            name="Teachers"
        )

        user.groups.add(
            teacher_group
        )

        # --------------------------------
        # CREATE TEACHER
        # --------------------------------

        Teacher.objects.create(

            user=user,

            school=school,

            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,

            gender=gender,
            phone=phone,
            email=email,

        )

        messages.success(
            request,
            f"{first_name} {last_name} "
            "was created successfully."
        )

        return redirect(
            "teacher_list"
        )

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/add_teacher.html",
        {
            "schools": schools,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def edit_teacher(request, id):

    # --------------------------------
    # GET TEACHER
    # --------------------------------

    if request.user.is_superuser:

        teacher = get_object_or_404(
            Teacher.objects.select_related("school", "user"),
            id=id,
        )

    else:

        school = request.user.school_user.school

        teacher = get_object_or_404(
            Teacher.objects.select_related("school", "user"),
            id=id,
            school=school,
        )

    # --------------------------------
    # POST
    # --------------------------------

    if request.method == "POST":

        employee_number = request.POST.get(
            "employee_number",
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

        gender = request.POST.get(
            "gender"
        )

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        # --------------------------------
        # EMPLOYEE NUMBER CHECK
        # --------------------------------

        if Teacher.objects.filter(
            employee_number=employee_number
        ).exclude(
            id=teacher.id
        ).exists():

            messages.error(
                request,
                "Employee number already exists."
            )

            return redirect(
                "edit_teacher",
                id=teacher.id,
            )

        # --------------------------------
        # UPDATE TEACHER
        # --------------------------------

        teacher.employee_number = employee_number
        teacher.first_name = first_name
        teacher.last_name = last_name
        teacher.gender = gender
        teacher.phone = phone
        teacher.email = email

        teacher.save()

        # --------------------------------
        # UPDATE LOGIN USER
        # --------------------------------

        if teacher.user:

            teacher.user.first_name = first_name
            teacher.user.last_name = last_name
            teacher.user.email = email

            teacher.user.save()

        messages.success(
            request,
            "Teacher updated successfully."
        )

        return redirect(
            "teacher_list"
        )

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/edit_teacher.html",
        {
            "teacher": teacher,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_teacher(request, id):

    # --------------------------------
    # GET TEACHER
    # --------------------------------

    if request.user.is_superuser:

        teacher = get_object_or_404(
            Teacher.objects.select_related(
                "school",
                "user",
            ),
            id=id,
        )

    else:

        school = request.user.school_user.school

        teacher = get_object_or_404(
            Teacher.objects.select_related(
                "school",
                "user",
            ),
            id=id,
            school=school,
        )

    # --------------------------------
    # DELETE
    # --------------------------------

    if request.method == "POST":

        # Keep reference to the linked login account
        user = teacher.user

        teacher.delete()

        # Delete the teacher's login account too
        if user:
            user.delete()

        messages.success(
            request,
            "Teacher deleted successfully."
        )

        return redirect("teacher_list")

    # --------------------------------
    # CONFIRMATION PAGE
    # --------------------------------

    return render(
        request,
        "students/delete_teacher.html",
        {
            "teacher": teacher,
        },
    )
@login_required
@admin_or_bursar
def subject_list(request):

    if request.user.is_superuser:
        subjects = Subject.objects.select_related(
            "school",
            "school_class",
            "teacher",
        ).all()

    else:
        school = request.user.school_user.school

        subjects = Subject.objects.select_related(
            "school",
            "school_class",
            "teacher",
        ).filter(
            school=school
        )

    return render(
        request,
        "students/subject_list.html",
        {
            "subjects": subjects,
        },
    )



@login_required
@admin_or_bursar
def add_subject(request):

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all()

        classes = SchoolClass.objects.select_related(
            "school"
        ).all()

        teachers = Teacher.objects.select_related(
            "school"
        ).all()

    else:

        school = request.user.school_user.school

        schools = [school]

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by("name")

        teachers = Teacher.objects.filter(
            school=school
        ).order_by("first_name", "last_name")

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        school_class_id = request.POST.get("school_class")
        teacher_id = request.POST.get("teacher")

        # -------------------------
        # DETERMINE SCHOOL
        # -------------------------

        if request.user.is_superuser:

            school_id = request.POST.get("school")

            if not school_id:
                messages.error(
                    request,
                    "Please select a school."
                )
                return redirect("add_subject")

            school = SchoolProfile.objects.filter(
                id=school_id
            ).first()

            if not school:
                messages.error(
                    request,
                    "Invalid school selected."
                )
                return redirect("add_subject")

        else:

            school = request.user.school_user.school

        # -------------------------
        # VALIDATE CLASS
        # -------------------------

        school_class = None

        if school_class_id:

            school_class = SchoolClass.objects.filter(
                id=school_class_id,
                school=school,
            ).first()

            if not school_class:
                messages.error(
                    request,
                    "Invalid class selected for this school."
                )
                return redirect("add_subject")

        # -------------------------
        # VALIDATE TEACHER
        # -------------------------

        teacher = None

        if teacher_id:

            teacher = Teacher.objects.filter(
                id=teacher_id,
                school=school,
            ).first()

            if not teacher:
                messages.error(
                    request,
                    "Invalid teacher selected for this school."
                )
                return redirect("add_subject")

        # -------------------------
        # CREATE SUBJECT
        # -------------------------

        Subject.objects.create(
            name=name,
            code=code,
            school=school,
            school_class=school_class,
            teacher=teacher,
        )

        messages.success(
            request,
            "Subject added successfully."
        )

        return redirect("subject_list")

    return render(
        request,
        "students/add_subject.html",
        {
            "schools": schools,
            "classes": classes,
            "teachers": teachers,
        },
    )
@login_required
@admin_or_bursar
def edit_subject(request, id):

    # --------------------------------
    # GET SUBJECT FOR THIS SCHOOL
    # --------------------------------

    if request.user.is_superuser:

        subject = get_object_or_404(
            Subject,
            id=id,
        )

        schools = SchoolProfile.objects.all()

        classes = SchoolClass.objects.select_related(
            "school"
        ).all()

        teachers = Teacher.objects.select_related(
            "school"
        ).all()

    else:

        school = request.user.school_user.school

        subject = get_object_or_404(
            Subject,
            id=id,
            school=school,
        )

        schools = [school]

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by("name")

        teachers = Teacher.objects.filter(
            school=school
        ).order_by(
            "first_name",
            "last_name",
        )

    # --------------------------------
    # SAVE CHANGES
    # --------------------------------

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        code = request.POST.get(
            "code",
            ""
        ).strip()

        school_class_id = request.POST.get(
            "school_class"
        )

        teacher_id = request.POST.get(
            "teacher"
        )

        # --------------------------------
        # DETERMINE SCHOOL
        # --------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get(
                "school"
            )

            if not school_id:
                messages.error(
                    request,
                    "Please select a school."
                )
                return redirect(
                    "edit_subject",
                    id=id,
                )

            school = SchoolProfile.objects.filter(
                id=school_id
            ).first()

            if not school:
                messages.error(
                    request,
                    "Invalid school selected."
                )
                return redirect(
                    "edit_subject",
                    id=id,
                )

        else:

            school = request.user.school_user.school

        # --------------------------------
        # VALIDATE CLASS
        # --------------------------------

        school_class = None

        if school_class_id:

            school_class = SchoolClass.objects.filter(
                id=school_class_id,
                school=school,
            ).first()

            if not school_class:
                messages.error(
                    request,
                    "Invalid class selected for this school."
                )
                return redirect(
                    "edit_subject",
                    id=id,
                )

        # --------------------------------
        # VALIDATE TEACHER
        # --------------------------------

        teacher = None

        if teacher_id:

            teacher = Teacher.objects.filter(
                id=teacher_id,
                school=school,
            ).first()

            if not teacher:
                messages.error(
                    request,
                    "Invalid teacher selected for this school."
                )
                return redirect(
                    "edit_subject",
                    id=id,
                )

        # --------------------------------
        # UPDATE SUBJECT
        # --------------------------------

        subject.name = name
        subject.code = code
        subject.school = school
        subject.school_class = school_class
        subject.teacher = teacher

        subject.save()

        messages.success(
            request,
            "Subject updated successfully."
        )

        return redirect(
            "subject_list"
        )

    # --------------------------------
    # DISPLAY FORM
    # --------------------------------

    return render(
        request,
        "students/edit_subject.html",
        {
            "subject": subject,
            "schools": schools,
            "classes": classes,
            "teachers": teachers,
        },
    )


@login_required
@admin_or_bursar
def delete_subject(request, id):

    if request.user.is_superuser:

        subject = get_object_or_404(
            Subject,
            id=id,
        )

    else:

        school = request.user.school_user.school

        subject = get_object_or_404(
            Subject,
            id=id,
            school=school,
        )

    if request.method == "POST":

        subject_name = subject.name

        subject.delete()

        messages.success(
            request,
            f"{subject_name} has been deleted successfully."
        )

        return redirect("subject_list")

    return render(
        request,
        "students/delete_subject.html",
        {
            "subject": subject,
        },
    )
@login_required
@admin_or_bursar
def class_list(request):

    if request.user.is_superuser:
        classes = SchoolClass.objects.select_related(
            "school",
            "class_teacher",
        ).all()

    else:
        school_user = request.user.school_user

        classes = SchoolClass.objects.select_related(
            "school",
            "class_teacher",
        ).filter(
            school=school_user.school
        )

    return render(
        request,
        "students/class_list.html",
        {
            "classes": classes,
        },
    )
@login_required
@admin_or_bursar
def add_class(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        teacher_id = request.POST.get("class_teacher")

        if not name:
            messages.error(request, "Class name is required.")
            return redirect("add_class")

        # Determine school
        if request.user.is_superuser:
            school_id = request.POST.get("school")

            if not school_id:
                messages.error(request, "Please select a school.")
                return redirect("add_class")

            school = SchoolProfile.objects.get(id=school_id)

        else:
            school_user = request.user.school_user
            school = school_user.school

        # Prevent duplicate class within the same school
        if SchoolClass.objects.filter(
            school=school,
            name=name,
        ).exists():
            messages.error(
                request,
                f"{name} already exists in {school.name}."
            )
            return redirect("add_class")

        class_teacher = None

        if teacher_id:
            class_teacher = Teacher.objects.filter(
                id=teacher_id,
                school=school,
            ).first()

            if not class_teacher:
                messages.error(
                    request,
                    "Invalid class teacher."
                )
                return redirect("add_class")

        SchoolClass.objects.create(
            school=school,
            name=name,
            class_teacher=class_teacher,
        )

        messages.success(
            request,
            f"{name} has been added successfully."
        )

        return redirect("class_list")

    # -------------------------
    # GET
    # -------------------------

    if request.user.is_superuser:
        schools = SchoolProfile.objects.all()
        teachers = Teacher.objects.all()
    else:
        school = request.user.school_user.school

        schools = [school]

        teachers = Teacher.objects.filter(
            school=school
        )

    return render(
        request,
        "students/add_class.html",
        {
            "schools": schools,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def edit_class(request, id):

    # --------------------------------
    # GET CLASS
    # --------------------------------

    if request.user.is_superuser:

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
        )

    else:

        school = request.user.school_user.school

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
            school=school,
        )

    # --------------------------------
    # POST
    # --------------------------------

    if request.method == "POST":

        teacher = None

        teacher_id = request.POST.get(
            "class_teacher"
        )

        if teacher_id:

            teacher = get_object_or_404(
                Teacher,
                id=teacher_id,
                school=school_class.school,
            )

        school_class.name = request.POST.get(
            "name",
            ""
        ).strip()

        school_class.class_teacher = teacher

        school_class.save()

        messages.success(
            request,
            "Class updated successfully."
        )

        return redirect("class_list")

    # --------------------------------
    # TEACHERS
    # --------------------------------

    teachers = Teacher.objects.filter(
        school=school_class.school
    ).order_by(
        "first_name",
        "last_name",
    )

    return render(
        request,
        "students/edit_class.html",
        {
            "school_class": school_class,
            "teachers": teachers,
        },
    )
@login_required
@admin_or_bursar
def delete_class(request, id):

    # --------------------------------
    # GET CLASS
    # --------------------------------

    if request.user.is_superuser:

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
        )

    else:

        school = request.user.school_user.school

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
            school=school,
        )

    # --------------------------------
    # DELETE
    # --------------------------------

    if request.method == "POST":

        class_name = school_class.name

        school_class.delete()

        messages.success(
            request,
            f"{class_name} deleted successfully."
        )

        return redirect("class_list")

    # --------------------------------
    # CONFIRMATION PAGE
    # --------------------------------

    return render(
        request,
        "students/delete_class.html",
        {
            "school_class": school_class,
        },
    )


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
    "Secretaries",
)
def attendance_list(request):

    # =====================================================
    # SUPERUSER
    # =====================================================

    if request.user.is_superuser:

        attendances = Attendance.objects.select_related(
            "student",
            "school_class",
            "school",
        )

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

    # =====================================================
    # SCHOOL USER
    # =====================================================

    else:

        # ---------------------------------------------
        # GET SCHOOL USER
        # ---------------------------------------------

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

        # ---------------------------------------------
        # ONLY ATTENDANCE FROM THIS SCHOOL
        # ---------------------------------------------

        attendances = Attendance.objects.select_related(
            "student",
            "school_class",
            "school",
        ).filter(
            school=school
        )

        # ---------------------------------------------
        # ONLY CLASSES FROM THIS SCHOOL
        # ---------------------------------------------

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    # =====================================================
    # FILTER BY CLASS
    # =====================================================

    school_class_id = request.GET.get(
        "school_class"
    )

    if school_class_id:

        attendances = attendances.filter(
            school_class_id=school_class_id
        )

    # =====================================================
    # FILTER BY DATE
    # =====================================================

    attendance_date = request.GET.get(
        "date"
    )

    if attendance_date:

        attendances = attendances.filter(
            date=attendance_date
        )

    # =====================================================
    # ORDER ATTENDANCE
    # =====================================================

    attendances = attendances.order_by(
        "-date",
        "school_class__name",
        "student__admission_number",
    )

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "students/attendance_list.html",
        {
            "attendances": attendances,
            "classes": classes,
        },
    )



@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
    "Secretaries",
)
def add_attendance(request):

    # --------------------------------
    # GET USER SCHOOL
    # --------------------------------

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # --------------------------------
    # GET CLASSES
    # --------------------------------

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

    else:

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    # --------------------------------
    # DEFAULT VALUES
    # --------------------------------

    selected_class = None

    students = []

    selected_date = (
        request.GET.get("date")
        or date.today().isoformat()
    )

    # --------------------------------
    # GET SELECTED CLASS
    # --------------------------------

    class_id = request.GET.get(
        "school_class"
    )

    if class_id:

        if request.user.is_superuser:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

        else:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=school,
            )

        students = Student.objects.filter(
            school_class=selected_class,
        ).order_by(
            "admission_number"
        )

    # --------------------------------
    # SAVE ALL ATTENDANCE
    # --------------------------------

    if request.method == "POST":

        class_id = request.POST.get(
            "school_class"
        )

        attendance_date = request.POST.get(
            "date"
        )

        if not class_id or not attendance_date:

            messages.error(
                request,
                "Class and date are required."
            )

            return redirect(
                "take_attendance"
            )

        # --------------------------------
        # GET CLASS SECURELY
        # --------------------------------

        if request.user.is_superuser:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

        else:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=school,
            )

        # --------------------------------
        # GET STUDENTS
        # --------------------------------

        students = Student.objects.filter(
            school_class=selected_class,
        ).order_by(
            "admission_number"
        )

        # --------------------------------
        # SAVE EACH STUDENT
        # --------------------------------

        for student in students:

            status = request.POST.get(
                f"status_{student.id}"
            )

            remarks = request.POST.get(
                f"remarks_{student.id}",
                ""
            ).strip()

            if status:

                Attendance.objects.update_or_create(

                    student=student,

                    date=attendance_date,

                    defaults={
                        "school": selected_class.school,
                        "school_class": selected_class,
                        "status": status,
                        "remarks": remarks,
                    },
                )

        messages.success(
            request,
            "Attendance saved successfully."
        )

        return redirect(
            "attendance_list"
        )

    # --------------------------------
    # LOAD EXISTING ATTENDANCE
    # --------------------------------

    attendance_map = {}

    if selected_class:

        records = Attendance.objects.filter(
            school_class=selected_class,
            date=selected_date,
        )

        attendance_map = {
            record.student_id: record
            for record in records
        }

        for student in students:

            student.attendance_record = (
                attendance_map.get(student.id)
            )

    else:

        for student in students:

            student.attendance_record = None

    # --------------------------------
    # RENDER
    # --------------------------------

    return render(
        request,
        "students/add_attendance.html",
        {
            "classes": classes,
            "selected_class": selected_class,
            "students": students,
            "selected_date": selected_date,
            "existing_attendance": attendance_map,
        },
    )





@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
    "Secretaries",
)
def take_attendance(request):

    # --------------------------------
    # GET USER'S SCHOOL
    # --------------------------------

    if request.user.is_superuser:
        school = None

    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:
            messages.error(
                request,
                "Your account is not linked to a school."
            )
            return redirect("home")

        school = school_user.school

    # --------------------------------
    # GET CLASSES
    # --------------------------------

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

    else:

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    students = None
    selected_class = None
    selected_date = request.GET.get(
        "date"
    ) or date.today().isoformat()

    # --------------------------------
    # LOAD STUDENTS
    # --------------------------------

    if request.method == "GET":

        class_id = request.GET.get(
            "school_class"
        )

        if class_id:

            # -------------------------
            # SUPERUSER
            # -------------------------

            if request.user.is_superuser:

                selected_class = get_object_or_404(
                    SchoolClass,
                    id=class_id,
                )

            # -------------------------
            # SCHOOL USER
            # -------------------------

            else:

                selected_class = get_object_or_404(
                    SchoolClass,
                    id=class_id,
                    school=school,
                )

            # -------------------------
            # GET STUDENTS
            # -------------------------

            students = Student.objects.filter(
                school_class=selected_class
            ).order_by(
                "admission_number"
            )

    # --------------------------------
    # SAVE ATTENDANCE
    # --------------------------------

    elif request.method == "POST":

        class_id = request.POST.get(
            "school_class"
        )

        attendance_date = request.POST.get(
            "date"
        )

        if not class_id or not attendance_date:

            messages.error(
                request,
                "Class and date are required."
            )

            return redirect(
                "take_attendance"
            )

        # -------------------------
        # GET CLASS SECURELY
        # -------------------------

        if request.user.is_superuser:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

        else:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=school,
            )

        # -------------------------
        # GET STUDENTS
        # -------------------------

        students = Student.objects.filter(
            school_class=selected_class
        ).order_by(
            "admission_number"
        )

        # -------------------------
        # SAVE EACH STUDENT
        # -------------------------

        for student in students:

            status = request.POST.get(
                f"status_{student.id}"
            )

            remarks = request.POST.get(
                f"remarks_{student.id}",
                ""
            ).strip()

            if status:

                Attendance.objects.update_or_create(

                    student=student,

                    date=attendance_date,

                    defaults={
                        "school_class": selected_class,
                        "school": selected_class.school,
                        "status": status,
                        "remarks": remarks,
                    },
                )

        messages.success(
            request,
            "Attendance saved successfully."
        )

        return redirect(
            "take_attendance"
        )

    # --------------------------------
    # LOAD EXISTING ATTENDANCE
    # --------------------------------

    attendance_map = {}

    if selected_class:

        records = Attendance.objects.filter(
            school_class=selected_class,
            date=selected_date,
        )

        attendance_map = {
            record.student_id: record
            for record in records
        }

        for student in students:

            student.attendance_record = (
                attendance_map.get(student.id)
            )

    # --------------------------------
    # RENDER
    # --------------------------------

    return render(
        request,
        "students/take_attendance.html",
        {
            "classes": classes,
            "students": students,
            "selected_class": selected_class,
            "selected_date": selected_date,
            "today": date.today(),
            "attendance_map": attendance_map,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def edit_attendance(request, id):

    # --------------------------------
    # GET ATTENDANCE SECURELY
    # --------------------------------

    if request.user.is_superuser:

        attendance = get_object_or_404(
            Attendance,
            id=id,
        )

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

        attendance = get_object_or_404(
            Attendance,
            id=id,
            school=school,
        )

    # --------------------------------
    # UPDATE ATTENDANCE
    # --------------------------------

    if request.method == "POST":

        attendance.status = request.POST.get(
            "status"
        )

        attendance.remarks = request.POST.get(
            "remarks",
            ""
        ).strip()

        attendance.save()

        messages.success(
            request,
            "Attendance updated successfully."
        )

        return redirect(
            "attendance_list"
        )

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/edit_attendance.html",
        {
            "attendance": attendance,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_attendance(request, id):

    # --------------------------------
    # GET ATTENDANCE SECURELY
    # --------------------------------

    if request.user.is_superuser:

        attendance = get_object_or_404(
            Attendance,
            id=id,
        )

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

        attendance = get_object_or_404(
            Attendance,
            id=id,
            school=school,
        )

    # --------------------------------
    # DELETE
    # --------------------------------

    if request.method == "POST":

        attendance.delete()

        messages.success(
            request,
            "Attendance deleted successfully."
        )

        return redirect(
            "attendance_list"
        )

    # --------------------------------
    # CONFIRMATION PAGE
    # --------------------------------

    return render(
        request,
        "students/delete_attendance.html",
        {
            "attendance": attendance,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def print_attendance(request):

    # =====================================================
    # GET USER'S SCHOOL
    # =====================================================

    if request.user.is_superuser:

        school = None

        attendances = Attendance.objects.select_related(
            "student",
            "school_class",
            "school",
        )

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

        # ---------------------------------------------
        # ONLY THIS SCHOOL'S ATTENDANCE
        # ---------------------------------------------

        attendances = Attendance.objects.select_related(
            "student",
            "school_class",
            "school",
        ).filter(
            school=school
        )

    # =====================================================
    # FILTER BY CLASS
    # =====================================================

    school_class = request.GET.get(
        "school_class"
    )

    if school_class:

        attendances = attendances.filter(
            school_class_id=school_class
        )

    # =====================================================
    # FILTER BY DATE
    # =====================================================

    attendance_date = request.GET.get(
        "date"
    )

    if attendance_date:

        attendances = attendances.filter(
            date=attendance_date
        )

    # =====================================================
    # ORDER
    # =====================================================

    attendances = attendances.order_by(
        "-date",
        "school_class__name",
        "student__admission_number",
    )

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "students/attendance_print.html",
        {
            "attendances": attendances,
            "school_class": school_class,
            "date": attendance_date,
        },
    )
@login_required
@admin_or_teacher
def add_timetable(request):

    if request.method == "POST":

        school_class = SchoolClass.objects.get(
            id=request.POST["school_class"]
        )

        subject = Subject.objects.get(
            id=request.POST["subject"]
        )

        teacher = Teacher.objects.get(
            id=request.POST["teacher"]
        )

        Timetable.objects.create(
            school_class=school_class,
            subject=subject,
            teacher=teacher,
            day=request.POST["day"],
            start_time=request.POST["start_time"],
            end_time=request.POST["end_time"],
        )

        return redirect("timetable_list")

    return render(
        request,
        "students/add_timetable.html",
        {
            "classes": SchoolClass.objects.all(),
            "subjects": Subject.objects.all(),
            "teachers": Teacher.objects.all(),
        },
    )


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def timetable_list(request):

    timetables = Timetable.objects.all()

    return render(
        request,
        "students/timetable_list.html",
        {
            "timetables": timetables
        },
    )
@login_required
@admin_required
def edit_timetable(request, id):

    timetable = get_object_or_404(Timetable, id=id)

    if request.method == "POST":

        timetable.school_class = SchoolClass.objects.get(
            id=request.POST["school_class"]
        )

        timetable.subject = Subject.objects.get(
            id=request.POST["subject"]
        )

        timetable.teacher = Teacher.objects.get(
            id=request.POST["teacher"]
        )

        timetable.day = request.POST["day"]
        timetable.start_time = request.POST["start_time"]
        timetable.end_time = request.POST["end_time"]

        timetable.save()

        return redirect("timetable_list")

    return render(
        request,
        "students/edit_timetable.html",
        {
            "timetable": timetable,
            "classes": SchoolClass.objects.all(),
            "subjects": Subject.objects.all(),
            "teachers": Teacher.objects.all(),
        },
    )
@login_required
@admin_required
def delete_timetable(request, id):

    timetable = get_object_or_404(Timetable, id=id)

    if request.method == "POST":
        timetable.delete()
        return redirect("timetable_list")

    return render(
        request,
        "students/delete_timetable.html",
        {
            "timetable": timetable,
        },
    )


@login_required
@in_group("Administrators", "Head Teacher", "Senior Teacher")
def print_timetable(request):
    timetables = Timetable.objects.select_related(
        "school_class",
        "subject",
        "teacher",
    ).order_by(
        "school_class__name",
        "day",
        "start_time",
    )

    school = SchoolProfile.objects.first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    if school:
        story.append(Paragraph(f"<b>{school.name}</b>", styles["Title"]))

    story.append(Paragraph("<b>School Timetable</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.08 * inch))

    data = [[
        "Class",
        "Subject",
        "Teacher",
        "Day",
        "Start",
        "End",
    ]]

    for t in timetables:
        data.append([
            t.school_class.name,
            t.subject.name,
            f"{t.teacher.first_name} {t.teacher.last_name}",
            t.day,
            str(t.start_time),
            str(t.end_time),
        ])

    table = Table(
        data,
        colWidths=[
            1.1 * inch,
            1.5 * inch,
            1.8 * inch,
            1.0 * inch,
            0.9 * inch,
            0.9 * inch,
        ],
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#1F4E79")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
    ]))

    story.append(table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="School_Timetable.pdf",
    )




    # Continue generating your PDF here
    # Generate PDF here

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
)
def exam_timetable_list(request):

    timetables = ExamTimetable.objects.select_related(
        "school_class",
        "exam",
        "subject",
        "supervisor",
    ).order_by(
        "school_class__name",
        "exam_date",
        "start_time",
    )

    return render(
        request,
        "students/exam_timetable_list.html",
        {
            "timetables": timetables,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
)
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
)
def print_exam_timetable(request):

    school = SchoolProfile.objects.first()

    timetables = ExamTimetable.objects.select_related(
        "school_class",
        "exam",
        "subject",
        "supervisor",
    ).order_by(
        "school_class__name",
        "exam_date",
        "start_time",
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = []

    if school:
        story.append(
            Paragraph(
                f"<b>{school.name}</b>",
                styles["Title"],
            )
        )

    story.append(
        Paragraph(
            "<b>School Examination Timetable</b>",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1,12))

    data = [[
        "Class",
        "Exam",
        "Subject",
        "Date",
        "Day",
        "Start",
        "End",
        "Room",
        "Supervisor",
    ]]

    for t in timetables:

        supervisor = ""

        if t.supervisor:
            supervisor = (
                f"{t.supervisor.first_name} "
                f"{t.supervisor.last_name}"
            )

        data.append([
            t.school_class.name,
            t.exam.name,
            t.subject.name,
            str(t.exam_date),
            t.day,
            str(t.start_time),
            str(t.end_time),
            t.room,
            supervisor,
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,0),8),
    ]))

    story.append(table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="School_Exam_Timetable.pdf",
    )


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def add_exam_timetable(request):

    # ==============================================
    # GET USER'S SCHOOL
    # ==============================================

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # ==============================================
    # GET SCHOOL-SPECIFIC DATA
    # ==============================================

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

        exams = Exam.objects.all().order_by(
            "name"
        )

        subjects = Subject.objects.all().order_by(
            "name"
        )

        teachers = Teacher.objects.all().order_by(
            "last_name",
            "first_name",
        )

    else:

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        exams = Exam.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        subjects = Subject.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        teachers = Teacher.objects.filter(
            school=school
        ).order_by(
            "last_name",
            "first_name",
        )

    # ==============================================
    # SAVE EXAM TIMETABLE
    # ==============================================

    if request.method == "POST":

        class_id = request.POST.get(
            "school_class"
        )

        exam_id = request.POST.get(
            "exam"
        )

        subject_id = request.POST.get(
            "subject"
        )

        supervisor_id = request.POST.get(
            "supervisor"
        )

        exam_date = request.POST.get(
            "exam_date"
        )

        day = request.POST.get(
            "day"
        )

        start_time = request.POST.get(
            "start_time"
        )

        end_time = request.POST.get(
            "end_time"
        )

        room = request.POST.get(
            "room",
            ""
        ).strip()

        # ==========================================
        # REQUIRED FIELDS
        # ==========================================

        if not all([
            class_id,
            exam_id,
            subject_id,
            exam_date,
            day,
            start_time,
            end_time,
        ]):

            messages.error(
                request,
                "Please fill in all required fields."
            )

            return redirect(
                "add_exam_timetable"
            )

        # ==========================================
        # GET OBJECTS SECURELY
        # ==========================================

        if request.user.is_superuser:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

            selected_exam = get_object_or_404(
                Exam,
                id=exam_id,
            )

            selected_subject = get_object_or_404(
                Subject,
                id=subject_id,
            )

            selected_teacher = None

            if supervisor_id:

                selected_teacher = get_object_or_404(
                    Teacher,
                    id=supervisor_id,
                )

        else:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=school,
            )

            selected_exam = get_object_or_404(
                Exam,
                id=exam_id,
                school=school,
            )

            selected_subject = get_object_or_404(
                Subject,
                id=subject_id,
                school=school,
            )

            selected_teacher = None

            if supervisor_id:

                selected_teacher = get_object_or_404(
                    Teacher,
                    id=supervisor_id,
                    school=school,
                )

        # ==========================================
        # CREATE RECORD
        # ==========================================

        ExamTimetable.objects.create(

            school=(
                selected_class.school
                if not request.user.is_superuser
                else selected_class.school
            ),

            school_class=selected_class,

            exam=selected_exam,

            subject=selected_subject,

            exam_date=exam_date,

            day=day,

            start_time=start_time,

            end_time=end_time,

            room=room,

            supervisor=selected_teacher,
        )

        messages.success(
            request,
            "Exam timetable added successfully."
        )

        return redirect(
            "exam_timetable_list"
        )

    # ==============================================
    # FORM
    # ==============================================

    return render(
        request,
        "students/add_exam_timetable.html",
        {
            "classes": classes,
            "exams": exams,
            "subjects": subjects,
            "teachers": teachers,
        },
    )



@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
)
def print_class_exam_timetable(request, id):

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # ==========================================
    # GET CLASS SECURELY
    # ==========================================

    if request.user.is_superuser:

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
        )

    else:

        school_class = get_object_or_404(
            SchoolClass,
            id=id,
            school=school,
        )

    # ==========================================
    # GET TIMETABLES
    # ==========================================

    if request.user.is_superuser:

        timetables = ExamTimetable.objects.filter(
            school_class=school_class,
        ).select_related(
            "school",
            "exam",
            "subject",
            "supervisor",
        ).order_by(
            "exam_date",
            "start_time",
        )

        # For superuser, get the school's actual school
        # instead of SchoolProfile.objects.first()

        school = school_class.school

    else:

        timetables = ExamTimetable.objects.filter(
            school=school,
            school_class=school_class,
        ).select_related(
            "exam",
            "subject",
            "supervisor",
        ).order_by(
            "exam_date",
            "start_time",
        )

    # ==========================================
    # CREATE PDF
    # ==========================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    story = []

    # ==========================================
    # SCHOOL NAME
    # ==========================================

    if school:

        story.append(
            Paragraph(
                f"<b>{school.name}</b>",
                styles["Title"],
            )
        )

    # ==========================================
    # CLASS TITLE
    # ==========================================

    story.append(
        Paragraph(
            f"<b>{school_class.name} Examination Timetable</b>",
            styles["Heading2"],
        )
    )

    story.append(
        Spacer(
            1,
            0.08 * inch,
        )
    )

    # ==========================================
    # TABLE HEADER
    # ==========================================

    data = [[
        "Exam",
        "Subject",
        "Date",
        "Day",
        "Start",
        "End",
        "Room",
        "Supervisor",
    ]]

    # ==========================================
    # TABLE DATA
    # ==========================================

    for timetable in timetables:

        supervisor = ""

        if timetable.supervisor:

            supervisor = (
                f"{timetable.supervisor.first_name} "
                f"{timetable.supervisor.last_name}"
            )

        data.append([
            timetable.exam.name,
            timetable.subject.name,
            str(timetable.exam_date),
            timetable.day,
            str(timetable.start_time),
            str(timetable.end_time),
            timetable.room or "-",
            supervisor or "-",
        ])

    # ==========================================
    # CREATE TABLE
    # ==========================================

    table = Table(
        data,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.darkblue,
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                8,
            ),

            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.beige,
            ),
        ])
    )

    story.append(table)

    # ==========================================
    # BUILD PDF
    # ==========================================

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=(
            f"{school_class.name}"
            "_Exam_Timetable.pdf"
        ),
    )

@login_required
@in_group("Administrators", "Head Teacher")
def edit_exam_timetable(request, id):

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # ==========================================
    # GET TIMETABLE SECURELY
    # ==========================================

    if request.user.is_superuser:

        timetable = get_object_or_404(
            ExamTimetable,
            id=id,
        )

    else:

        timetable = get_object_or_404(
            ExamTimetable,
            id=id,
            school=school,
        )

    # ==========================================
    # GET SCHOOL-SPECIFIC OPTIONS
    # ==========================================

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "name"
        )

        exams = Exam.objects.all().order_by(
            "name"
        )

        subjects = Subject.objects.all().order_by(
            "name"
        )

        teachers = Teacher.objects.all().order_by(
            "last_name",
            "first_name",
        )

    else:

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        exams = Exam.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        subjects = Subject.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        teachers = Teacher.objects.filter(
            school=school
        ).order_by(
            "last_name",
            "first_name",
        )

    # ==========================================
    # SAVE CHANGES
    # ==========================================

    if request.method == "POST":

        class_id = request.POST.get(
            "school_class"
        )

        exam_id = request.POST.get(
            "exam"
        )

        subject_id = request.POST.get(
            "subject"
        )

        supervisor_id = request.POST.get(
            "supervisor"
        )

        exam_date = request.POST.get(
            "exam_date"
        )

        day = request.POST.get(
            "day"
        )

        start_time = request.POST.get(
            "start_time"
        )

        end_time = request.POST.get(
            "end_time"
        )

        room = request.POST.get(
            "room",
            ""
        ).strip()

        # ==========================================
        # REQUIRED FIELDS
        # ==========================================

        if not all([
            class_id,
            exam_id,
            subject_id,
            exam_date,
            day,
            start_time,
            end_time,
        ]):

            messages.error(
                request,
                "Please fill in all required fields."
            )

            return redirect(
                "edit_exam_timetable",
                id=id,
            )

        # ==========================================
        # GET OBJECTS SECURELY
        # ==========================================

        if request.user.is_superuser:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

            selected_exam = get_object_or_404(
                Exam,
                id=exam_id,
            )

            selected_subject = get_object_or_404(
                Subject,
                id=subject_id,
            )

            selected_teacher = None

            if supervisor_id:

                selected_teacher = get_object_or_404(
                    Teacher,
                    id=supervisor_id,
                )

        else:

            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
                school=school,
            )

            selected_exam = get_object_or_404(
                Exam,
                id=exam_id,
                school=school,
            )

            selected_subject = get_object_or_404(
                Subject,
                id=subject_id,
                school=school,
            )

            selected_teacher = None

            if supervisor_id:

                selected_teacher = get_object_or_404(
                    Teacher,
                    id=supervisor_id,
                    school=school,
                )

        # ==========================================
        # KEEP TIMETABLE IN THE CORRECT SCHOOL
        # ==========================================

        timetable.school_class = selected_class
        timetable.exam = selected_exam
        timetable.subject = selected_subject

        timetable.exam_date = exam_date
        timetable.day = day
        timetable.start_time = start_time
        timetable.end_time = end_time
        timetable.room = room

        timetable.supervisor = selected_teacher

        # School is determined from the selected class.
        timetable.school = selected_class.school

        timetable.save()

        messages.success(
            request,
            "Exam timetable updated successfully."
        )

        return redirect(
            "exam_timetable_list"
        )

    # ==========================================
    # FORM
    # ==========================================

    return render(
        request,
        "students/edit_exam_timetable.html",
        {
            "timetable": timetable,
            "classes": classes,
            "exams": exams,
            "subjects": subjects,
            "teachers": teachers,
        },
    )
@login_required
@in_group("Administrators", "Head Teacher")
def delete_exam_timetable(request, id):

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("home")

        school = school_user.school

    # ==========================================
    # GET TIMETABLE SECURELY
    # ==========================================

    if request.user.is_superuser:

        timetable = get_object_or_404(
            ExamTimetable,
            id=id,
        )

    else:

        timetable = get_object_or_404(
            ExamTimetable,
            id=id,
            school=school,
        )

    # ==========================================
    # DELETE
    # ==========================================

    if request.method == "POST":

        timetable.delete()

        messages.success(
            request,
            "Exam timetable deleted successfully."
        )

        return redirect(
            "exam_timetable_list"
        )

    # ==========================================
    # CONFIRMATION PAGE
    # ==========================================

    return render(
        request,
        "students/delete_exam_timetable.html",
        {
            "timetable": timetable,
        },
    )

@login_required
def load_exams(request):

    class_id = request.GET.get("class_id")

    if not class_id:
        return JsonResponse([], safe=False)

    # ==========================================
    # SUPERUSER
    # ==========================================

    if request.user.is_superuser:

        exams = Exam.objects.filter(
            school_class_id=class_id
        ).values(
            "id",
            "name",
        )

        return JsonResponse(
            list(exams),
            safe=False,
        )

    # ==========================================
    # GET USER'S SCHOOL
    # ==========================================

    school_user = getattr(
        request.user,
        "school_user",
        None,
    )

    if not school_user:

        return JsonResponse(
            {
                "error": "Your account is not linked to a school."
            },
            status=403,
        )

    school = school_user.school

    # ==========================================
    # VERIFY CLASS BELONGS TO SCHOOL
    # ==========================================

    selected_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=school,
    )

    # ==========================================
    # GET EXAMS
    # ==========================================

    exams = Exam.objects.filter(
        school=school,
        school_class=selected_class,
    ).values(
        "id",
        "name",
    )

    return JsonResponse(
        list(exams),
        safe=False,
    )

@login_required
def get_class_exams(request, class_id):

    # ==========================================
    # SUPERUSER
    # ==========================================

    if request.user.is_superuser:

        exams = Exam.objects.filter(
            school_class_id=class_id
        ).order_by(
            "name"
        )

    else:

        # ======================================
        # GET USER'S SCHOOL
        # ======================================

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            return JsonResponse(
                {
                    "error": (
                        "Your account is not linked "
                        "to a school."
                    )
                },
                status=403,
            )

        school = school_user.school

        # ======================================
        # VERIFY CLASS BELONGS TO SCHOOL
        # ======================================

        selected_class = get_object_or_404(
            SchoolClass,
            id=class_id,
            school=school,
        )

        # ======================================
        # GET SCHOOL EXAMS
        # ======================================

        exams = Exam.objects.filter(
            school=school,
            school_class=selected_class,
        ).order_by(
            "name"
        )

    # ==========================================
    # PREPARE JSON
    # ==========================================

    data = []

    for exam in exams:

        data.append({
            "id": exam.id,
            "name": exam.name,
            "term": exam.term,
        })

    return JsonResponse(
        data,
        safe=False,
    )