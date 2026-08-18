from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.lib import colors
from django.http import FileResponse
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib.enums import TA_CENTER
from django.db.models import Avg, Sum, Count
from django.http import HttpResponse
from decimal import Decimal
from django.db import transaction

from django.utils import timezone

from reportlab.pdfgen import canvas

from students.decorators import (
    admin_or_bursar,
    in_group,
    admin_or_teacher,
    admin_required
)

from students.utils import (
    draw_school_header,
    draw_school_footer,
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

from students.models import *



@login_required
def exam_list(request):

    if request.user.is_superuser:

        exams = Exam.objects.select_related(
            "school",
        ).all()

    else:

        school = request.user.school_user.school

        exams = Exam.objects.select_related(
            "school",
        ).filter(
            school=school
        )

    return render(
        request,
        "students/exam_list.html",
        {
            "exams": exams,
        },
    )


@login_required
@admin_or_bursar
def add_exam(request):

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

        name = request.POST.get(
            "name",
            ""
        ).strip()

        term = request.POST.get(
            "term",
            ""
        ).strip()

        year = request.POST.get(
            "year",
            ""
        ).strip()

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
                    "add_exam"
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
                    "add_exam"
                )

        else:

            school = request.user.school_user.school

        # --------------------------------
        # CREATE EXAM
        # --------------------------------

        Exam.objects.create(

            name=name,
            term=term,
            year=year,

            school=school,

            status="OPEN",
        )

        messages.success(
            request,
            "Exam created successfully."
        )

        return redirect(
            "exam_list"
        )

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/add_exam.html",
        {
            "schools": schools,
        },
    )
@login_required
@admin_or_bursar
def edit_exam(request, id):

    # --------------------------------
    # GET EXAM
    # --------------------------------

    if request.user.is_superuser:

        exam = get_object_or_404(
            Exam.objects.select_related("school"),
            id=id,
        )

    else:

        school = request.user.school_user.school

        exam = get_object_or_404(
            Exam.objects.select_related("school"),
            id=id,
            school=school,
        )

    # --------------------------------
    # POST
    # --------------------------------

    if request.method == "POST":

        exam.name = request.POST.get(
            "name",
            ""
        ).strip()

        exam.term = request.POST.get(
            "term",
            ""
        ).strip()

        exam.year = request.POST.get(
            "year"
        )

        exam.save()

        messages.success(
            request,
            "Exam updated successfully."
        )

        return redirect("exam_list")

    # --------------------------------
    # FORM
    # --------------------------------

    return render(
        request,
        "students/edit_exam.html",
        {
            "exam": exam,
        },
    )

@login_required
@admin_or_bursar
def delete_exam(request, id):

    # --------------------------------
    # GET EXAM
    # --------------------------------

    if request.user.is_superuser:

        exam = get_object_or_404(
            Exam.objects.select_related("school"),
            id=id,
        )

    else:

        school = request.user.school_user.school

        exam = get_object_or_404(
            Exam.objects.select_related("school"),
            id=id,
            school=school,
        )

    # --------------------------------
    # DELETE
    # --------------------------------

    if request.method == "POST":

        exam.delete()

        messages.success(
            request,
            "Exam deleted successfully."
        )

        return redirect("exam_list")

    # --------------------------------
    # CONFIRMATION PAGE
    # --------------------------------

    return render(
        request,
        "students/delete_exam.html",
        {
            "exam": exam,
        },
    )
# ==========================
# Marks
# ==========================
@login_required
@admin_or_teacher
def mark_list(request):

    # =====================================================
    # BASE QUERY
    # =====================================================

    marks = Mark.objects.select_related(
        "student",
        "student__school",
        "subject",
        "subject__school",
        "subject__teacher",
        "exam",
        "exam__school",
    )

    # =====================================================
    # SUPERUSER
    # =====================================================

    if request.user.is_superuser:

        marks = marks.all()

    # =====================================================
    # SCHOOL ADMINISTRATOR
    # =====================================================

    elif hasattr(request.user, "school_user"):

        school_user = request.user.school_user
        school = school_user.school

        marks = marks.filter(
            student__school=school,
            subject__school=school,
            exam__school=school,
        )

    # =====================================================
    # TEACHER
    # =====================================================

    elif hasattr(request.user, "teacher_profile"):

        teacher = request.user.teacher_profile
        school = teacher.school

        marks = marks.filter(
            subject__teacher=teacher,
            student__school=school,
            subject__school=school,
            exam__school=school,
        )

    # =====================================================
    # NO VALID PROFILE
    # =====================================================

    else:

        marks = Mark.objects.none()

    # =====================================================
    # DISPLAY
    # =====================================================

    return render(
        request,
        "students/mark_list.html",
        {
            "marks": marks,
        },
    )
@login_required
@admin_or_teacher
def add_mark(request):

    # =========================================================
    # DETERMINE USER'S SCHOOL
    # =========================================================

    if request.user.is_superuser:

        school = None

    elif hasattr(request.user, "school_user"):

        # Administrators and other school users
        # get their school from school_user.
        school = request.user.school_user.school

    else:

        # Teachers get their school from Teacher profile.
        teacher = Teacher.objects.filter(
            user=request.user
        ).select_related("school").first()

        if not teacher:

            messages.error(
                request,
                "Your account is not linked to a school or teacher."
            )

            return redirect("home")

        school = teacher.school


    # =========================================================
    # DETERMINE WHETHER USER IS ADMINISTRATOR
    # =========================================================

    is_administrator = request.user.groups.filter(
        name="Administrators"
    ).exists()


    # =========================================================
    # AVAILABLE CLASSES
    # =========================================================

    if request.user.is_superuser:

        classes = SchoolClass.objects.all().order_by(
            "school__name",
            "name",
        )

    elif is_administrator:

        # Administrator sees all classes in their school.
        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    else:

        # Teacher sees only classes where they teach.
        teacher = Teacher.objects.filter(
            user=request.user
        ).first()

        if teacher:

            classes = SchoolClass.objects.filter(
                school=school,
                subjects__teacher=teacher,
            ).distinct().order_by(
                "name"
            )

        else:

            classes = SchoolClass.objects.none()


    # =========================================================
    # OPEN EXAMS
    # =========================================================

    if request.user.is_superuser:

        exams = Exam.objects.filter(
            status="OPEN"
        ).select_related(
            "school"
        ).order_by(
            "year",
            "term",
            "name",
        )

    else:

        exams = Exam.objects.filter(
            school=school,
            status="OPEN",
        ).order_by(
            "year",
            "term",
            "name",
        )


    # =========================================================
    # INITIAL VALUES
    # =========================================================

    students = Student.objects.none()

    subjects = Subject.objects.none()

    selected_class = None
    selected_subject = None
    selected_exam = None


    # =========================================================
    # POST
    # =========================================================

    if request.method == "POST":

        class_id = request.POST.get(
            "school_class"
        )

        subject_id = request.POST.get(
            "subject"
        )

        exam_id = request.POST.get(
            "exam"
        )


        # =====================================================
        # VALIDATE CLASS
        # =====================================================

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


        # =====================================================
        # LOAD SUBJECTS FOR SELECTED CLASS
        # =====================================================

        if selected_class:

            if request.user.is_superuser:

                subjects = Subject.objects.filter(
                    school=selected_class.school,
                    school_class=selected_class,
                ).order_by(
                    "name"
                )

            elif is_administrator:

                subjects = Subject.objects.filter(
                    school=school,
                    school_class=selected_class,
                ).order_by(
                    "name"
                )

            else:

                teacher = Teacher.objects.filter(
                    user=request.user
                ).first()

                if teacher:

                    subjects = Subject.objects.filter(
                        school=school,
                        school_class=selected_class,
                        teacher=teacher,
                    ).order_by(
                        "name"
                    )

                else:

                    subjects = Subject.objects.none()


        # =====================================================
        # VALIDATE SUBJECT
        # =====================================================

        if subject_id and selected_class:

            if request.user.is_superuser:

                selected_subject = get_object_or_404(
                    Subject,
                    id=subject_id,
                    school=selected_class.school,
                    school_class=selected_class,
                )

            elif is_administrator:

                selected_subject = get_object_or_404(
                    Subject,
                    id=subject_id,
                    school=school,
                    school_class=selected_class,
                )

            else:

                teacher = Teacher.objects.filter(
                    user=request.user
                ).first()

                if not teacher:

                    messages.error(
                        request,
                        "Your account is not linked to a teacher."
                    )

                    return redirect(
                        "add_mark"
                    )

                selected_subject = get_object_or_404(
                    Subject,
                    id=subject_id,
                    school=school,
                    school_class=selected_class,
                    teacher=teacher,
                )


        # =====================================================
        # VALIDATE EXAM
        # =====================================================

        if exam_id:

            if request.user.is_superuser:

                selected_exam = get_object_or_404(
                    Exam,
                    id=exam_id,
                    status="OPEN",
                )

            else:

                selected_exam = get_object_or_404(
                    Exam,
                    id=exam_id,
                    school=school,
                    status="OPEN",
                )


        # =====================================================
        # LOAD STUDENTS
        # =====================================================

        if selected_class:

            if request.user.is_superuser:

                students = Student.objects.filter(
                    school_class=selected_class,
                    school=selected_class.school,
                ).order_by(
                    "admission_number"
                )

            else:

                students = Student.objects.filter(
                    school=school,
                    school_class=selected_class,
                ).order_by(
                    "admission_number"
                )


        # =====================================================
        # SAVE MARKS
        # =====================================================

        if (
            "save_marks" in request.POST
            and selected_class
            and selected_subject
            and selected_exam
        ):


            # =================================================
            # SCHOOL CONSISTENCY CHECK
            # =================================================

            if selected_subject.school != selected_exam.school:

                messages.error(
                    request,
                    "The selected subject and exam do not belong to the same school."
                )

                return redirect(
                    "add_mark"
                )


            if selected_class.school != selected_exam.school:

                messages.error(
                    request,
                    "The selected class and exam do not belong to the same school."
                )

                return redirect(
                    "add_mark"
                )


            # =================================================
            # DETERMINE TEACHER FOR SUBMISSION
            # =================================================

            if request.user.is_superuser:

                # Superuser uses the teacher assigned to
                # the subject.
                teacher = selected_subject.teacher

            elif is_administrator:

                # Administrator also uses the teacher assigned
                # to the subject.
                teacher = selected_subject.teacher

            else:

                # Normal teacher uses their own Teacher profile.
                teacher = Teacher.objects.filter(
                    user=request.user
                ).first()


            # =================================================
            # TEACHER REQUIRED
            # =================================================

            if not teacher:

                messages.error(
                    request,
                    "The selected subject does not have a teacher assigned."
                )

                return redirect(
                    "add_mark"
                )


            # =================================================
            # TEACHER / EXAM SCHOOL CHECK
            # =================================================

            if teacher.school != selected_exam.school:

                messages.error(
                    request,
                    "Teacher and exam do not belong to the same school."
                )

                return redirect(
                    "add_mark"
                )


            # =================================================
            # FIND OR CREATE MARK SUBMISSION
            # =================================================

            submission, created = MarkSubmission.objects.get_or_create(

                school_class=selected_class,

                subject=selected_subject,

                exam=selected_exam,

                defaults={
                    "teacher": teacher,
                    "status": "DRAFT",
                },
            )


            # =================================================
            # DO NOT EDIT APPROVED MARKS
            # =================================================

            if submission.status == "APPROVED":

                messages.error(
                    request,
                    "These marks have already been approved."
                )

                return redirect(
                    "add_mark"
                )


            # =================================================
            # DO NOT EDIT SUBMITTED MARKS
            # =================================================

            if submission.status == "SUBMITTED":

                messages.error(
                    request,
                    "These marks have already been submitted and are waiting for approval."
                )

                return redirect(
                    "add_mark"
                )


            # =================================================
            # REJECTED → RETURN TO DRAFT
            # =================================================

            if submission.status == "REJECTED":

                submission.status = "DRAFT"

                submission.teacher = teacher

                submission.save(
                    update_fields=[
                        "status",
                        "teacher",
                    ]
                )


            # =================================================
            # SAVE EACH STUDENT'S MARK
            # =================================================

            saved_count = 0

            for student in students:

                value = request.POST.get(
                    f"marks_{student.id}"
                )


                # ---------------------------------------------
                # EMPTY MARK
                # ---------------------------------------------

                if value in (None, ""):

                    continue


                # ---------------------------------------------
                # CONVERT MARK
                # ---------------------------------------------

                try:

                    mark_value = float(value)

                except (TypeError, ValueError):

                    messages.error(
                        request,
                        f"Invalid mark for "
                        f"{student.first_name} "
                        f"{student.last_name}."
                    )

                    continue


                # ---------------------------------------------
                # VALIDATE RANGE
                # ---------------------------------------------

                if mark_value < 0 or mark_value > 100:

                    messages.error(
                        request,
                        f"Mark for "
                        f"{student.first_name} "
                        f"{student.last_name} "
                        f"must be between 0 and 100."
                    )

                    continue


                # ---------------------------------------------
                # CALCULATE GRADE
                # ---------------------------------------------

                grade = calculate_grade(
                    mark_value
                )


                # ---------------------------------------------
                # CREATE OR UPDATE MARK
                # ---------------------------------------------

                Mark.objects.update_or_create(

                    student=student,

                    subject=selected_subject,

                    exam=selected_exam,

                    defaults={
                        "marks": mark_value,
                        "grade": grade,
                        "submission": submission,
                    },
                )

                saved_count += 1


            # =================================================
            # RESULT MESSAGE
            # =================================================

            if saved_count > 0:

                messages.success(
                    request,
                    f"{saved_count} mark(s) saved successfully."
                )

            else:

                messages.warning(
                    request,
                    "No marks were entered."
                )


            return redirect(
                "add_mark"
            )


    # =========================================================
    # RETURN FORM
    # =========================================================

    return render(
        request,
        "students/add_mark.html",
        {
            "classes": classes,
            "students": students,
            "subjects": subjects,
            "exams": exams,

            "selected_class": selected_class,
            "selected_subject": selected_subject,
            "selected_exam": selected_exam,
        },
    )
@login_required
@admin_or_teacher
def edit_mark(request, id):

    # --------------------------------
    # GET MARK
    # --------------------------------

    if request.user.is_superuser:

        mark = get_object_or_404(
            Mark.objects.select_related(
                "student",
                "student__school",
                "subject",
                "subject__school",
                "subject__school_class",
                "subject__teacher",
                "exam",
                "exam__school",
                "submission",
            ),
            id=id,
        )

    else:

        # --------------------------------
        # GET USER SCHOOL
        # --------------------------------

        if hasattr(request.user, "school_user"):

            school = request.user.school_user.school

        else:

            teacher = Teacher.objects.filter(
                user=request.user
            ).first()

            if not teacher:

                messages.error(
                    request,
                    "Your account is not linked to a school."
                )

                return redirect("mark_list")

            school = teacher.school

        # --------------------------------
        # GET MARK FROM SAME SCHOOL
        # --------------------------------

        mark = get_object_or_404(
            Mark.objects.select_related(
                "student",
                "student__school",
                "subject",
                "subject__school",
                "subject__school_class",
                "subject__teacher",
                "exam",
                "exam__school",
                "submission",
            ),
            id=id,
            student__school=school,
            subject__school=school,
            exam__school=school,
        )

    # --------------------------------
    # CHECK SUBMISSION STATUS
    # --------------------------------

    if mark.submission:

        if mark.submission.status == "APPROVED":

            messages.error(
                request,
                "Approved marks cannot be edited."
            )

            return redirect("mark_list")

        if mark.submission.status == "SUBMITTED":

            messages.error(
                request,
                "Submitted marks cannot be edited. "
                "Please wait for the administrator to review them."
            )

            return redirect("mark_list")

    # --------------------------------
    # TEACHER PERMISSION
    # --------------------------------

    teacher = None

    if not request.user.is_superuser:

        teacher = Teacher.objects.filter(
            user=request.user
        ).first()

        if not teacher:

            messages.error(
                request,
                "Your account is not linked to a teacher profile."
            )

            return redirect("mark_list")

        # Teacher can only edit marks
        # for their own subject

        if mark.subject.teacher_id != teacher.id:

            messages.error(
                request,
                "You can only edit marks for your own subjects."
            )

            return redirect("mark_list")

    # --------------------------------
    # SCHOOL
    # --------------------------------

    if request.user.is_superuser:

        school = mark.student.school

    # --------------------------------
    # SUBJECTS
    # --------------------------------

    if request.user.is_superuser:

        subjects = Subject.objects.filter(
            school=school
        ).select_related(
            "school_class",
            "teacher",
        ).order_by("name")

    else:

        subjects = Subject.objects.filter(
            school=school,
            teacher=teacher,
        ).select_related(
            "school_class",
            "teacher",
        ).order_by("name")

    # --------------------------------
    # STUDENTS
    # --------------------------------

    students = Student.objects.filter(
        school=school,
        school_class=mark.subject.school_class,
    ).order_by(
        "admission_number"
    )

    # --------------------------------
    # EXAMS
    # --------------------------------

    exams = Exam.objects.filter(
        school=school,
    ).order_by(
        "-year",
        "term",
        "name",
    )

    # --------------------------------
    # POST
    # --------------------------------

    if request.method == "POST":

        student_id = request.POST.get(
            "student"
        )

        subject_id = request.POST.get(
            "subject"
        )

        exam_id = request.POST.get(
            "exam"
        )

        marks_value = request.POST.get(
            "marks"
        )

        # --------------------------------
        # BASIC VALIDATION
        # --------------------------------

        if not student_id or not subject_id or not exam_id:

            messages.error(
                request,
                "Please complete all required fields."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        if marks_value in (
            None,
            "",
        ):

            messages.error(
                request,
                "Please enter marks."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        # --------------------------------
        # VALIDATE STUDENT
        # --------------------------------

        student = get_object_or_404(
            Student,
            id=student_id,
            school=school,
        )

        # --------------------------------
        # VALIDATE SUBJECT
        # --------------------------------

        if request.user.is_superuser:

            subject = get_object_or_404(
                Subject,
                id=subject_id,
                school=school,
            )

        else:

            subject = get_object_or_404(
                Subject,
                id=subject_id,
                school=school,
                teacher=teacher,
            )

        # --------------------------------
        # VALIDATE EXAM
        # --------------------------------

        exam = get_object_or_404(
            Exam,
            id=exam_id,
            school=school,
        )

        # --------------------------------
        # MARKS VALIDATION
        # --------------------------------

        try:

            marks_value = float(
                marks_value
            )

        except ValueError:

            messages.error(
                request,
                "Marks must be a valid number."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        if marks_value < 0 or marks_value > 100:

            messages.error(
                request,
                "Marks must be between 0 and 100."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        # --------------------------------
        # STUDENT / SUBJECT CLASS CHECK
        # --------------------------------

        if student.school_class_id != subject.school_class_id:

            messages.error(
                request,
                "The selected student does not belong "
                "to the selected subject's class."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        # --------------------------------
        # CHECK DUPLICATE MARK
        # --------------------------------

        duplicate = Mark.objects.filter(
            student=student,
            subject=subject,
            exam=exam,
        ).exclude(
            id=mark.id
        ).exists()

        if duplicate:

            messages.error(
                request,
                "A mark already exists for this student, "
                "subject and exam."
            )

            return redirect(
                "edit_mark",
                id=mark.id,
            )

        # --------------------------------
        # UPDATE MARK
        # --------------------------------

        mark.student = student
        mark.subject = subject
        mark.exam = exam
        mark.marks = marks_value
        mark.grade = calculate_grade(
            marks_value
        )

        mark.save()

        messages.success(
            request,
            "Marks updated successfully."
        )

        return redirect(
            "mark_list"
        )

    # --------------------------------
    # DISPLAY FORM
    # --------------------------------

    return render(
        request,
        "students/edit_mark.html",
        {
            "mark": mark,
            "students": students,
            "subjects": subjects,
            "exams": exams,
        },
    )
@login_required
@admin_or_teacher
def delete_mark(request, id):

    # --------------------------------
    # GET MARK
    # --------------------------------

    if request.user.is_superuser:

        mark = get_object_or_404(
            Mark.objects.select_related(
                "student",
                "student__school",
                "subject",
                "subject__school",
                "exam",
                "exam__school",
                "submission",
            ),
            id=id,
        )

    else:

        # --------------------------------
        # GET USER'S SCHOOL
        # --------------------------------

        if hasattr(request.user, "school_user"):

            school = request.user.school_user.school

        else:

            teacher = Teacher.objects.filter(
                user=request.user
            ).first()

            if not teacher:

                messages.error(
                    request,
                    "Your account is not linked to a school or teacher profile."
                )

                return redirect("mark_list")

            school = teacher.school

        # --------------------------------
        # GET MARK FROM SAME SCHOOL
        # --------------------------------

        mark = get_object_or_404(
            Mark.objects.select_related(
                "student",
                "student__school",
                "subject",
                "subject__school",
                "exam",
                "exam__school",
                "submission",
            ),
            id=id,
            student__school=school,
            subject__school=school,
            exam__school=school,
        )

        # --------------------------------
        # TEACHER PERMISSION
        # --------------------------------

        teacher = Teacher.objects.filter(
            user=request.user
        ).first()

        if teacher:

            # Teacher can only delete marks
            # belonging to their own subject

            if mark.subject.teacher_id != teacher.id:

                messages.error(
                    request,
                    "You can only delete marks for your own subjects."
                )

                return redirect("mark_list")

    # --------------------------------
    # PREVENT DELETING APPROVED MARKS
    # --------------------------------

    if mark.submission:

        if mark.submission.status == "APPROVED":

            messages.error(
                request,
                "Approved marks cannot be deleted."
            )

            return redirect("mark_list")

    # --------------------------------
    # DELETE
    # --------------------------------

    if request.method == "POST":

        mark.delete()

        messages.success(
            request,
            "Mark deleted successfully."
        )

        return redirect("mark_list")

    # --------------------------------
    # CONFIRMATION PAGE
    # --------------------------------

    return render(
        request,
        "students/delete_mark.html",
        {
            "mark": mark,
        },
    )

def calculate_grade(mark):
    if mark >= 80:
        return "A"
    elif mark >= 75:
        return "A-"
    elif mark >= 70:
        return "B+"
    elif mark >= 65:
        return "B"
    elif mark >= 60:
        return "B-"
    elif mark >= 55:
        return "C+"
    elif mark >= 50:
        return "C"
    elif mark >= 45:
        return "C-"
    elif mark >= 40:
        return "D+"
    elif mark >= 35:
        return "D"
    else:
        return "E"

@login_required
@admin_or_teacher
def submit_mark(request, id):

    mark = get_object_or_404(Mark, id=id)

    if not request.user.is_superuser:
        if mark.subject.teacher != request.user.teacher_profile:
            messages.error(
                request,
                "You cannot submit another teacher's marks."
            )
            return redirect("mark_list")

    mark.status = "SUBMITTED"
    mark.save()

    messages.success(
        request,
        "Marks submitted successfully."
    )

    return redirect("mark_list")

@login_required
@admin_or_teacher
def mark_submission_list(request):

    # --------------------------------
    # SUPERUSER
    # --------------------------------

    if request.user.is_superuser:

        submissions = (
            MarkSubmission.objects
            .select_related(
                "teacher",
                "school_class",
                "school_class__school",
                "subject",
                "subject__school",
                "exam",
                "exam__school",
            )
            .all()
            .order_by("-id")
        )

    else:

        # --------------------------------
        # GET SCHOOL
        # --------------------------------

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
        # GET TEACHER PROFILE
        # --------------------------------

        teacher = Teacher.objects.filter(
            user=request.user,
            school=school,
        ).first()

        # --------------------------------
        # TEACHER
        # --------------------------------

        if teacher:

            submissions = (
                MarkSubmission.objects
                .select_related(
                    "teacher",
                    "school_class",
                    "school_class__school",
                    "subject",
                    "subject__school",
                    "exam",
                    "exam__school",
                )
                .filter(
                    teacher=teacher,
                    school_class__school=school,
                    subject__school=school,
                    exam__school=school,
                )
                .order_by("-id")
            )

        # --------------------------------
        # SCHOOL ADMINISTRATOR
        # --------------------------------

        else:

            submissions = (
                MarkSubmission.objects
                .select_related(
                    "teacher",
                    "school_class",
                    "school_class__school",
                    "subject",
                    "subject__school",
                    "exam",
                    "exam__school",
                )
                .filter(
                    school_class__school=school,
                    subject__school=school,
                    exam__school=school,
                )
                .order_by("-id")
            )

    return render(
        request,
        "students/mark_submission_list.html",
        {
            "submissions": submissions,
        },
    )
@login_required
@admin_or_teacher
def submit_mark_submission(request, id):

    # --------------------------------
    # GET TEACHER
    # --------------------------------

    teacher = Teacher.objects.filter(
        user=request.user
    ).first()

    # --------------------------------
    # GET SUBMISSION
    # --------------------------------

    if request.user.is_superuser:

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
        )

    elif teacher:

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
            teacher=teacher,
            school_class__school=teacher.school,
            subject__school=teacher.school,
            exam__school=teacher.school,
        )

    else:

        messages.error(
            request,
            "Your account is not linked to a teacher profile."
        )

        return redirect("mark_submission_list")

    # --------------------------------
    # CHECK STATUS
    # --------------------------------

    if submission.status != "DRAFT":

        messages.warning(
            request,
            "This submission has already been submitted."
        )

        return redirect("mark_submission_list")

    # --------------------------------
    # SUBMIT
    # --------------------------------

    submission.status = "SUBMITTED"

    submission.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Class marks submitted successfully."
    )

    return redirect("mark_submission_list")
@login_required
@admin_or_bursar
def admin_mark_submission_list(request):

    # --------------------------------
    # SUPERUSER
    # --------------------------------

    if request.user.is_superuser:

        submissions = (
            MarkSubmission.objects
            .filter(status="SUBMITTED")
            .select_related(
                "school_class",
                "school_class__school",
                "subject",
                "subject__school",
                "exam",
                "exam__school",
                "teacher",
            )
            .prefetch_related("marks")
            .order_by("-id")
        )

    # --------------------------------
    # NORMAL SCHOOL ADMIN/BURSAR
    # --------------------------------

    else:

        school = request.user.school_user.school

        submissions = (
            MarkSubmission.objects
            .filter(
                status="SUBMITTED",
                school_class__school=school,
                subject__school=school,
                exam__school=school,
            )
            .select_related(
                "school_class",
                "school_class__school",
                "subject",
                "subject__school",
                "exam",
                "exam__school",
                "teacher",
            )
            .prefetch_related("marks")
            .order_by("-id")
        )

    return render(
        request,
        "students/admin_mark_submission_list.html",
        {
            "submissions": submissions,
        },
    )

@login_required
@admin_or_bursar
def approve_mark_submission(request, id):

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request."
        )
        return redirect("admin_mark_submission_list")

    # --------------------------------
    # GET SUBMISSION
    # --------------------------------

    if request.user.is_superuser:

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
            status="SUBMITTED",
        )

    else:

        school = request.user.school_user.school

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
            status="SUBMITTED",
            school_class__school=school,
            subject__school=school,
            exam__school=school,
        )

    # --------------------------------
    # APPROVE
    # --------------------------------

    submission.status = "APPROVED"
    submission.approved_by = request.user
    submission.approved_at = timezone.now()

    submission.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
        ]
    )

    messages.success(
        request,
        "Marks approved successfully."
    )

    return redirect("admin_mark_submission_list")
@login_required
@admin_or_bursar
def reject_mark_submission(request, id):

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request."
        )
        return redirect("admin_mark_submission_list")

    # --------------------------------
    # GET SUBMISSION
    # --------------------------------

    if request.user.is_superuser:

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
            status="SUBMITTED",
        )

    else:

        school = request.user.school_user.school

        submission = get_object_or_404(
            MarkSubmission,
            id=id,
            status="SUBMITTED",
            school_class__school=school,
            subject__school=school,
            exam__school=school,
        )

    # --------------------------------
    # REJECT
    # --------------------------------

    submission.status = "REJECTED"

    submission.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Marks rejected successfully."
    )

    return redirect(
        "admin_mark_submission_list"
    )
@login_required
@admin_or_bursar
def view_mark_submission(request, id):

    submission = get_object_or_404(
        MarkSubmission,
        id=id,
    )

    marks = Mark.objects.filter(
        submission=submission
    ).select_related(
        "student",
        "subject",
        "exam",
    ).order_by(
        "student__admission_number"
    )

    return render(
        request,
        "students/view_mark_submission.html",
        {
            "submission": submission,
            "marks": marks,
        },
    )

@login_required
@admin_or_teacher
def teacher_draft_submissions(request):

    if request.user.is_superuser:
        submissions = MarkSubmission.objects.filter(
            status="DRAFT"
        )
    else:
        teacher = request.user.teacher_profile

        submissions = MarkSubmission.objects.filter(
            teacher=teacher,
            status="DRAFT",
        )

    return render(
        request,
        "students/teacher_draft_submissions.html",
        {
            "submissions": submissions,
        },
    )

@login_required
@admin_or_teacher
def continue_mark_entry(request, id):

    submission = get_object_or_404(
        MarkSubmission,
        id=id,
    )

    # --------------------------------
    # TEACHER PERMISSION
    # --------------------------------

    if (
        not request.user.is_superuser
        and submission.teacher != request.user.teacher_profile
    ):
        messages.error(
            request,
            "You cannot edit another teacher's marks."
        )

        return redirect("mark_submission_list")

    # --------------------------------
    # ONLY DRAFT OR REJECTED
    # --------------------------------

    if submission.status not in ["DRAFT", "REJECTED"]:

        messages.error(
            request,
            "This submission cannot be edited."
        )

        return redirect("mark_submission_list")

    # --------------------------------
    # EXISTING MARKS
    # --------------------------------

    marks = Mark.objects.filter(
        submission=submission
    ).select_related(
        "student"
    ).order_by(
        "student__admission_number"
    )

    # --------------------------------
    # SAVE CORRECTED MARKS
    # --------------------------------

    if request.method == "POST":

        for mark in marks:

            value = request.POST.get(
                f"mark_{mark.id}"
            )

            # Empty field
            if value in [None, ""]:
                continue

            try:

                value = float(value)

            except (TypeError, ValueError):

                messages.error(
                    request,
                    f"Invalid mark for "
                    f"{mark.student.first_name} "
                    f"{mark.student.last_name}."
                )

                return render(
                    request,
                    "students/edit_mark_draft.html",
                    {
                        "submission": submission,
                        "marks": marks,
                    },
                )

            # --------------------------------
            # VALIDATE MARK
            # --------------------------------

            if value < 0 or value > 100:

                messages.error(
                    request,
                    "Marks must be between 0 and 100."
                )

                return render(
                    request,
                    "students/edit_mark_draft.html",
                    {
                        "submission": submission,
                        "marks": marks,
                    },
                )

            # --------------------------------
            # UPDATE MARK
            # --------------------------------

            mark.marks = value
            mark.grade = calculate_grade(value)
            mark.save()

        # --------------------------------
        # REJECTED → DRAFT
        # --------------------------------

        if submission.status == "REJECTED":

            submission.status = "DRAFT"
            submission.save(
                update_fields=["status"]
            )

        messages.success(
            request,
            "Marks corrected successfully. "
            "The submission is now a draft and can be submitted again."
        )

        return redirect(
            "mark_submission_list"
        )

    # --------------------------------
    # DISPLAY EXISTING MARKS
    # --------------------------------

    return render(
        request,
        "students/edit_mark_draft.html",
        {
            "submission": submission,
            "marks": marks,
        },
    )






@login_required
@admin_or_teacher
def student_report(request, id):

    if request.user.is_superuser:

        student = get_object_or_404(
            Student,
            id=id,
        )

    else:

        school = request.user.school_user.school

        student = get_object_or_404(
            Student,
            id=id,
            school=school,
        )

    school = student.school

    marks = Mark.objects.filter(student=student).select_related(
        "subject",
        "exam",
    )

    # Current exam
    exam = None
    if marks.exists():
        exam = marks.first().exam

    # Total Marks
    total = sum(mark.marks for mark in marks)

    # Average
    if marks.exists():
        average = round(total / marks.count(), 2)
    else:
        average = 0

    # Overall Grade
    if average >= 80:
        overall_grade = "A"

    elif average >= 75:
        overall_grade = "A-"

    elif average >= 70:
        overall_grade = "B+"

    elif average >= 65:
        overall_grade = "B"

    elif average >= 60:
        overall_grade = "B-"

    elif average >= 55:
        overall_grade = "C+"

    elif average >= 50:
        overall_grade = "C"

    elif average >= 45:
        overall_grade = "C-"

    elif average >= 40:
        overall_grade = "D+"

    elif average >= 35:
        overall_grade = "D"

    else:
        overall_grade = "E"

    # Position in class
    position = 1
    class_size = 1

    if exam:

        classmates = Student.objects.filter(
            school_class=student.school_class
        )

        averages = []

        for s in classmates:

            class_marks = Mark.objects.filter(
                student=s,
                exam=exam
            ).select_related("subject")

            if class_marks.exists():

                avg = (
                    class_marks.aggregate(
                        Avg("marks")
                    )["marks__avg"]
                )

            else:
                avg = 0

            averages.append(
                (s.id, avg)
            )

        averages.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        class_size = len(averages)

        for index, item in enumerate(averages):

            if item[0] == student.id:
                position = index + 1
                break

    # Fee Summary
    total_fee = student.total_fee()

    total_paid = student.total_paid()

    balance = student.balance()

    # Teacher Remarks
    if average >= 80:
        remark = "Excellent Performance. Keep it up."

    elif average >= 70:
        remark = "Very Good Performance."

    elif average >= 60:
        remark = "Good Work. Keep improving."

    elif average >= 50:
        remark = "Fair Performance."

    else:
        remark = "Needs more effort."

    context = {

        "school": school,

        "student": student,

        "exam": exam,

        "marks": marks,

        "total": total,

        "average": average,

        "overall_grade": overall_grade,

        "position": position,

        "class_size": class_size,

        "remark": remark,

        "total_fee": total_fee,

        "total_paid": total_paid,

        "balance": balance,
    }

    return render(
        request,
        "students/student_report.html",
        context,
    )

def calculate_overall_grade(average):
    if average >= 80:
        return "A"
    elif average >= 75:
        return "A-"
    elif average >= 70:
        return "B+"
    elif average >= 65:
        return "B"
    elif average >= 60:
        return "B-"
    elif average >= 55:
        return "C+"
    elif average >= 50:
        return "C"
    elif average >= 45:
        return "C-"
    elif average >= 40:
        return "D+"
    elif average >= 35:
        return "D"
    else:
        return "E"



    


@login_required
def print_report(request, id):

    # ==========================================
    # GET STUDENT
    # ==========================================

    if request.user.is_superuser:

        student = get_object_or_404(
            Student.objects.select_related(
                "school",
                "school_class",
            ),
            id=id,
        )

    else:

        # --------------------------------------
        # GET USER SCHOOL
        # --------------------------------------

        if hasattr(request.user, "school_user"):

            school = request.user.school_user.school

        elif hasattr(request.user, "teacher_profile"):

            school = request.user.teacher_profile.school

        else:

            teacher = Teacher.objects.filter(
                user=request.user
            ).first()

            if teacher:

                school = teacher.school

            else:

                messages.error(
                    request,
                    "Your account is not linked to a school."
                )

                return redirect("home")

        # --------------------------------------
        # GET STUDENT FROM SAME SCHOOL
        # --------------------------------------

        student = get_object_or_404(
            Student.objects.select_related(
                "school",
                "school_class",
            ),
            id=id,
            school=school,
        )

    # ==========================================
    # SCHOOL
    # ==========================================

    school = student.school

    # ==========================================
    # GET MARKS
    # ==========================================

    marks = Mark.objects.filter(
        student=student,
        student__school=school,
        subject__school=school,
        exam__school=school,
    ).select_related(
        "subject",
        "exam",
    ).order_by(
        "subject__name"
    )

    # ==========================================
    # GET EXAM
    # ==========================================

    exam = marks.first().exam if marks.exists() else None

    # ==========================================
    # TOTAL & AVERAGE
    # ==========================================

    total = sum(
        mark.marks
        for mark in marks
    )

    average = (
        round(
            total / marks.count(),
            2,
        )
        if marks.exists()
        else 0
    )

    # ==========================================
    # OVERALL GRADE
    # ==========================================

    overall_grade = calculate_overall_grade(
        average
    )

    # ==========================================
    # CLASS POSITION
    # ==========================================

    students = Student.objects.filter(
        school=school,
        school_class=student.school_class,
    )

    results = []

    for s in students:

        if exam:

            student_marks = Mark.objects.filter(
                student=s,
                exam=exam,
                student__school=school,
                subject__school=school,
                exam__school=school,
            )

        else:

            student_marks = Mark.objects.filter(
                student=s,
                student__school=school,
                subject__school=school,
            )

        if student_marks.exists():

            average_marks = (
                sum(
                    m.marks
                    for m in student_marks
                )
                / student_marks.count()
            )

        else:

            average_marks = 0

        results.append(
            (
                s.id,
                average_marks,
            )
        )

    # ==========================================
    # SORT RESULTS
    # ==========================================

    results.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    # ==========================================
    # FIND STUDENT POSITION
    # ==========================================

    position = 0

    for index, item in enumerate(
        results,
        start=1,
    ):

        if item[0] == student.id:

            position = index
            break

    class_size = len(results)

    # ==========================================
    # PDF BUFFER
    # ==========================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        topMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )

    # ==========================================
    # STYLES
    # ==========================================

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    normal = styles["Normal"]
    normal.alignment = TA_CENTER

    italic = styles["Italic"]
    italic.alignment = TA_CENTER

    story = []

    # ==========================================
    # SCHOOL LOGO
    # ==========================================

    logo = ""

    if school and school.logo:

        try:

            logo = Image(
                school.logo.path,
                width=45,
                height=45,
            )

        except Exception:

            logo = ""

    # ==========================================
    # SCHOOL INFORMATION
    # ==========================================

    school_info = Paragraph(
        f"""
        <font size=16>
            <b>{school.name}</b>
        </font>
        <br/>
        <font size=9>
            {school.motto or ""}
        </font>
        <br/>
        <font size=9>
            {school.address or ""}
        </font>
        <br/>
        <font size=9>
            Tel: {school.phone or ""}
        </font>
        <br/>
        <font size=9>
            {school.email or ""}
        </font>
        <br/>
        <font size=9>
            {school.current_term or ""}
            |
            {school.academic_year or ""}
        </font>
        """,
        styles["Normal"],
    )

    # ==========================================
    # HEADER
    # ==========================================

    header = Table(
        [
            [
                logo,
                school_info,
            ]
        ],
        colWidths=[
            0.8 * inch,
            6.0 * inch,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (0, 0),
                    "LEFT",
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(header)

    story.append(
        Spacer(
            1,
            0.05 * inch,
        )
    )

    # ==========================================
    # STUDENT INFORMATION
    # ==========================================

    student_info = [

        [
            "Admission No",
            student.admission_number,
        ],

        [
            "Student Name",
            f"{student.first_name} {student.last_name}",
        ],

        [
            "Gender",
            student.gender,
        ],

        [
            "Class",
            str(student.school_class),
        ],

        [
            "Date of Birth",
            str(student.date_of_birth),
        ],

        [
            "Exam",
            str(exam) if exam else "N/A",
        ],

    ]

    info_table = Table(
        student_info,
        colWidths=[
            2 * inch,
            4 * inch,
        ],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    HexColor("#D9EAD3"),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),

                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    # ==========================================
    # STUDENT PHOTO
    # ==========================================

    photo = ""

    if student.photo:

        try:

            photo = Image(
                student.photo.path,
                width=0.9 * inch,
                height=1.1 * inch,
            )

        except Exception:

            photo = ""

    # ==========================================
    # DETAILS + PHOTO
    # ==========================================

    details = Table(
        [
            [
                info_table,
                photo,
            ]
        ],
        colWidths=[
            5.1 * inch,
            1.7 * inch,
        ],
    )

    details.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    # ==========================================
    # MARKS TABLE
    # ==========================================

    data = [
        [
            "No",
            "Subject",
            "Marks",
            "Grade",
        ]
    ]

    for index, mark in enumerate(
        marks,
        start=1,
    ):

        data.append(
            [
                index,
                mark.subject.name,
                mark.marks,
                mark.grade,
            ]
        )

    # ==========================================
    # SUMMARY
    # ==========================================

    data.append(
        [
            "",
            "",
            "",
            "",
        ]
    )

    data.append(
        [
            "",
            "TOTAL",
            total,
            "",
        ]
    )

    data.append(
        [
            "",
            "AVERAGE",
            average,
            overall_grade,
        ]
    )

    data.append(
        [
            "",
            "POSITION",
            f"{position} of {class_size}",
            "",
        ]
    )

    results_table = Table(
        data,
        colWidths=[
            0.7 * inch,
            3.8 * inch,
            0.8 * inch,
            0.8 * inch,
        ],
    )

    results_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    HexColor("#1F4E79"),
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
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
                    4,
                ),

                (
                    "BACKGROUND",
                    (0, -3),
                    (-1, -3),
                    colors.lightgrey,
                ),

                (
                    "BACKGROUND",
                    (0, -2),
                    (-1, -2),
                    HexColor("#D9EAD3"),
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    HexColor("#FFF2CC"),
                ),

                (
                    "FONTNAME",
                    (0, -3),
                    (-1, -1),
                    "Helvetica-Bold",
                ),

                (
                    "ALIGN",
                    (1, -3),
                    (1, -1),
                    "LEFT",
                ),
            ]
        )
    )

    # ==========================================
    # MAIN TABLE
    # ==========================================

    main_table = Table(
        [
            [details],
            [results_table],
        ],
        colWidths=[
            6.8 * inch
        ],
    )

    main_table.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT",
                ),
            ]
        )
    )

    story.append(main_table)

    story.append(
        Spacer(
            1,
            0.08 * inch,
        )
    )

    # ==========================================
    # TEACHER REMARK
    # ==========================================

    if average >= 80:

        teacher_remark = (
            "Excellent Performance. Keep it up."
        )

    elif average >= 70:

        teacher_remark = (
            "Very Good Performance."
        )

    elif average >= 60:

        teacher_remark = (
            "Good Work. Keep Improving."
        )

    elif average >= 50:

        teacher_remark = (
            "Fair Performance."
        )

    else:

        teacher_remark = (
            "Needs More Effort."
        )

    # ==========================================
    # PRINCIPAL REMARK
    # ==========================================

    if average >= 80:

        principal_remark = (
            "Excellent performance. "
            "Keep up the outstanding work."
        )

    elif average >= 70:

        principal_remark = (
            "Very good performance. "
            "Continue working hard."
        )

    elif average >= 60:

        principal_remark = (
            "Good performance. "
            "Aim even higher next term."
        )

    elif average >= 50:

        principal_remark = (
            "Fair performance. "
            "More effort will lead to better results."
        )

    else:

        principal_remark = (
            "Needs improvement. "
            "Work harder and remain focused."
        )

    # ==========================================
    # FEE SUMMARY
    # ==========================================

    total_fee = student.total_fee()
    total_paid = student.total_paid()
    balance = student.balance()

    story.append(
        Paragraph(
            "<b>FEE SUMMARY</b>",
            styles["Heading2"],
        )
    )

    fee_data = [

        [
            "Total Fee",
            f"KSh {total_fee}",
        ],

        [
            "Amount Paid",
            f"KSh {total_paid}",
        ],

        [
            "Balance",
            f"KSh {balance}",
        ],

    ]

    fee_table = Table(
        fee_data,
        colWidths=[
            2.5 * inch,
            2 * inch,
        ],
    )

    fee_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    HexColor("#dff0d8"),
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(fee_table)

    story.append(
        Spacer(
            1,
            0.12 * inch,
        )
    )

    # ==========================================
    # REMARKS
    # ==========================================

    remarks_table = Table(
        [
            [
                Paragraph(
                    "<b>Teacher's Remarks</b>",
                    styles["Heading3"],
                ),

                Paragraph(
                    "<b>Principal's Remarks</b>",
                    styles["Heading3"],
                ),
            ],

            [
                Paragraph(
                    teacher_remark,
                    styles["Normal"],
                ),

                Paragraph(
                    principal_remark,
                    styles["Normal"],
                ),
            ],
        ],
        colWidths=[
            3.3 * inch,
            3.3 * inch,
        ],
    )

    remarks_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(remarks_table)

    story.append(
        Spacer(
            1,
            0.15 * inch,
        )
    )

    # ==========================================
    # SIGNATURE SECTION
    # ==========================================

    signature = ""

    if school and school.principal_signature:

        try:

            signature = Image(
                school.principal_signature.path,
                width=120,
                height=50,
            )

        except Exception:

            signature = ""

    signature_table = Table(
        [
            [
                "__________________________",
                signature,
            ],

            [
                "Class Teacher",
                school.principal_name or "Principal",
            ],
        ],
        colWidths=[
            3.3 * inch,
            3.3 * inch,
        ],
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(signature_table)

    story.append(
        Spacer(
            1,
            0.08 * inch,
        )
    )

    # ==========================================
    # FOOTER
    # ==========================================

    story.append(
        Paragraph(
            "Generated by School Management System",
            styles["Italic"],
        )
    )

    # ==========================================
    # BUILD PDF
    # ==========================================

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=(
            f"{student.admission_number}_Report.pdf"
        ),
        content_type="application/pdf",
    )

@login_required
@admin_or_bursar
def class_results(request):

    school = request.user.school_user.school

    # Only show this school's data
    classes = SchoolClass.objects.filter(
        school=school
    ).order_by("name")

    exams = Exam.objects.filter(
        school=school
    ).order_by("-id")

    selected_class = None
    selected_exam = None

    results = []
    subjects = []
    subject_analysis = []

    student_count = 0
    class_average = 0
    highest_total = 0
    lowest_total = 0

    if request.method == "POST":

        selected_class = get_object_or_404(
            SchoolClass,
            id=request.POST["school_class"],
            school=school,
        )

        selected_exam = get_object_or_404(
            Exam,
            id=request.POST["exam"],
            school=school,
        )

        # Students belonging to this school and selected class
        students = Student.objects.filter(
            school=school,
            school_class=selected_class,
        ).order_by("first_name", "last_name")

        # Subjects belonging to this school
        subjects = Subject.objects.filter(
            school=school
        ).order_by("name")

        # --------------------------------
        # STUDENT RESULTS
        # --------------------------------

        for student in students:

            student_marks = {}
            total = 0
            subjects_with_marks = 0

            for subject in subjects:

                mark = Mark.objects.filter(
                    student=student,
                    subject=subject,
                    exam=selected_exam,
                    school=school,
                ).first()

                if mark:
                    student_marks[subject.id] = mark.marks
                    total += mark.marks
                    subjects_with_marks += 1
                else:
                    student_marks[subject.id] = "-"

            average = (
                total / subjects_with_marks
                if subjects_with_marks
                else 0
            )

            results.append({
                "student": student,
                "marks": student_marks,
                "total": total,
                "average": round(average, 2),
                "grade": calculate_grade(average),
            })

        # --------------------------------
        # SORT BY TOTAL
        # --------------------------------

        results.sort(
            key=lambda x: x["total"],
            reverse=True
        )

        # --------------------------------
        # POSITIONS
        # --------------------------------

        for i, row in enumerate(results, start=1):
            row["position"] = i

        # --------------------------------
        # SUMMARY
        # --------------------------------

        student_count = len(results)

        if results:

            class_average = round(
                sum(
                    r["average"]
                    for r in results
                ) / student_count,
                2
            )

            highest_total = results[0]["total"]
            lowest_total = results[-1]["total"]

        # --------------------------------
        # SUBJECT ANALYSIS
        # --------------------------------

        for subject in subjects:

            subject_marks = Mark.objects.filter(
                school=school,
                subject=subject,
                exam=selected_exam,
                student__school=school,
                student__school_class=selected_class,
            )

            if subject_marks.exists():

                highest = (
                    subject_marks
                    .order_by("-marks")
                    .first()
                    .marks
                )

                lowest = (
                    subject_marks
                    .order_by("marks")
                    .first()
                    .marks
                )

                average = round(
                    subject_marks.aggregate(
                        Avg("marks")
                    )["marks__avg"],
                    2
                )

            else:

                highest = "-"
                lowest = "-"
                average = "-"

            subject_analysis.append({
                "subject": subject,
                "teacher": subject.teacher,
                "highest": highest,
                "lowest": lowest,
                "average": average,
            })

    return render(
        request,
        "students/class_results.html",
        {
            "classes": classes,
            "exams": exams,
            "subjects": subjects,
            "results": results,
            "selected_class": selected_class,
            "selected_exam": selected_exam,

            "student_count": student_count,
            "class_average": class_average,
            "highest_total": highest_total,
            "lowest_total": lowest_total,

            "subject_analysis": subject_analysis,
        },
    )
@login_required
@admin_or_bursar
def print_class_results(request):

    class_id = request.GET.get("class")
    exam_id = request.GET.get("exam")

    selected_class = get_object_or_404(
        SchoolClass,
        id=class_id
    )

    selected_exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    students = Student.objects.filter(
        school_class=selected_class
    )

    subjects = Subject.objects.all().order_by("name")

    results = []

    for student in students:

        student_marks = {}
        total = 0

        for subject in subjects:

            mark = Mark.objects.filter(
                student=student,
                subject=subject,
                exam=selected_exam
            ).first()

            if mark:
                student_marks[subject.id] = mark.marks
                total += mark.marks
            else:
                student_marks[subject.id] = "-"

        average = total / len(subjects) if subjects else 0

        results.append({
            "student": student,
            "marks": student_marks,
            "total": total,
            "average": round(average, 2),
            "grade": calculate_grade(average),
        })

    results.sort(
        key=lambda x: x["total"],
        reverse=True
    )

    for i, row in enumerate(results, start=1):
        row["position"] = i

    return render(
        request,
        "students/print_class_results.html",
        {
            "selected_class": selected_class,
            "selected_exam": selected_exam,
            "subjects": subjects,
            "results": results,
        },
    )

@login_required
@admin_or_bursar
def toggle_exam_status(request, id):
    exam = get_object_or_404(Exam, id=id)

    if exam.status == "OPEN":
        exam.status = "CLOSED"
    else:
        exam.status = "OPEN"

    exam.save()

    return redirect("exam_list")
