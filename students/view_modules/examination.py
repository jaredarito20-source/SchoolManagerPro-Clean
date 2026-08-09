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
    if request.user.is_superuser:
        marks = Mark.objects.all()
    else:
        teacher = request.user.teacher_profile
        marks = Mark.objects.filter(subject__teacher=teacher)


    return render(request, "students/mark_list.html", {
        "marks": marks
    })


@login_required
@admin_or_teacher
def add_mark(request):

    if request.user.is_superuser:
        classes = SchoolClass.objects.all()
    else:
        teacher = request.user.teacher_profile
        classes = SchoolClass.objects.filter(
            subjects__teacher=teacher
        ).distinct()

    exams = Exam.objects.filter(status="OPEN")

    students = Student.objects.none()
    subjects = Subject.objects.none()
    selected_class = None

    if request.method == "POST":

        class_id = request.POST.get("school_class")

        if class_id:
            selected_class = get_object_or_404(
                SchoolClass,
                id=class_id,
            )

            students = Student.objects.filter(
                school_class=selected_class
            ).order_by(
                "admission_number"
            )

            if request.user.is_superuser:
                subjects = Subject.objects.filter(
                    school_class=selected_class
                )
            else:
                teacher = request.user.teacher_profile

                subjects = Subject.objects.filter(
                    school_class=selected_class,
                    teacher=teacher,
                )

        # Only loading students
        if "save_marks" not in request.POST:

            return render(
                request,
                "students/add_mark.html",
                {
                    "classes": classes,
                    "students": students,
                    "subjects": subjects,
                    "exams": exams,
                    "selected_class": selected_class,
                },
            )

        subject = get_object_or_404(
            Subject,
            id=request.POST["subject"],
        )

        exam = get_object_or_404(
            Exam,
            id=request.POST["exam"],
        )

        if request.user.is_superuser:
            teacher = subject.teacher
        else:
            teacher = request.user.teacher_profile

        submission, created = MarkSubmission.objects.get_or_create(
            school_class=selected_class,
            subject=subject,
            exam=exam,
            defaults={
                "teacher": teacher,
                "status": "DRAFT",
            },
        )

        if (
            not request.user.is_superuser
            and submission.status != "DRAFT"
        ):
            messages.error(
                request,
                "This submission has already been submitted."
            )
            return redirect("mark_list")

        for student in students:

            value = request.POST.get(
                f"marks_{student.id}"
            )

            if value in [None, ""]:
                continue

            marks = float(value)

            Mark.objects.update_or_create(
                student=student,
                subject=subject,
                exam=exam,
                defaults={
                    "submission": submission,
                    "marks": marks,
                    "grade": calculate_grade(marks),
                },
            )

        messages.success(
            request,
            "Class marks saved successfully."
        )

        return redirect("add_mark")

    return render(
        request,
        "students/add_mark.html",
        {
            "classes": classes,
            "students": students,
            "subjects": subjects,
            "exams": exams,
            "selected_class": selected_class,
        },
    )
@login_required
@admin_or_teacher
def edit_mark(request, id):
    mark = get_object_or_404(Mark, id=id)

    # Prevent teachers from editing other teachers' marks
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the administrator can edit marks."
        )
        return redirect("mark_list")
    # Subjects
    if request.user.is_superuser:
        subjects = Subject.objects.all()
    else:
        teacher = request.user.teacher_profile
        subjects = Subject.objects.filter(teacher=teacher)

    # Students
    if request.user.is_superuser:
        students = Student.objects.filter(
            school_class=mark.subject.school_class
        )
    else:
        students = Student.objects.filter(
            school_class=mark.subject.school_class
        )

    exams = Exam.objects.all()

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"],
        )

        if request.user.is_superuser:
            subject = get_object_or_404(
                Subject,
                id=request.POST["subject"],
            )
        else:
            subject = get_object_or_404(
                Subject,
                id=request.POST["subject"],
                teacher=request.user.teacher_profile,
            )

        exam = get_object_or_404(
            Exam,
            id=request.POST["exam"],
        )

        marks = float(request.POST["marks"])

        # Ensure student belongs to the selected subject's class
        if student.school_class != subject.school_class:
            messages.error(
                request,
                "The selected student does not belong to this subject's class."
            )
            return redirect("edit_mark", id=mark.id)

        mark.student = student
        mark.subject = subject
        mark.exam = exam
        mark.marks = marks
        mark.grade = calculate_grade(marks)
        mark.save()

        messages.success(
            request,
            "Marks updated successfully."
        )

        return redirect("mark_list")

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
    mark = get_object_or_404(Mark, id=id)

    # Teachers can only delete marks for their own subjects
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only the administrator can delete marks."
        )
        return redirect("mark_list")
        if request.method == "POST":
            mark.delete()
            messages.success(request, "Mark deleted successfully.")
            return redirect("mark_list")

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

    if request.user.is_superuser:
        submissions = MarkSubmission.objects.all()

    else:
        teacher = request.user.teacher_profile

        submissions = MarkSubmission.objects.filter(
            teacher=teacher
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

    submission = get_object_or_404(
        MarkSubmission,
        id=id,
    )

    if (
        not request.user.is_superuser
        and submission.teacher != request.user.teacher_profile
    ):
        messages.error(
            request,
            "You cannot submit another teacher's marks."
        )
        return redirect("mark_submission_list")

    if submission.status != "DRAFT":
        messages.warning(
            request,
            "This submission has already been submitted."
        )
        return redirect("mark_submission_list")

    submission.status = "SUBMITTED"
    submission.save()

    messages.success(
        request,
        "Class marks submitted successfully."
    )

    return redirect("mark_submission_list")

@login_required
@admin_or_bursar
def admin_mark_submission_list(request):

    submissions = MarkSubmission.objects.filter(
        status="SUBMITTED"
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

    submission = get_object_or_404(
        MarkSubmission,
        id=id,
    )

    submission.status = "APPROVED"
    submission.approved_by = request.user
    submission.approved_at = timezone.now()
    submission.save()

    messages.success(
        request,
        "Marks approved successfully."
    )

    return redirect("admin_mark_submission_list")

@login_required
@admin_or_bursar
def reject_mark_submission(request, id):

    submission = get_object_or_404(
        MarkSubmission,
        id=id,
    )

    submission.status = "REJECTED"
    submission.save()

    messages.warning(
        request,
        "Submission rejected."
    )

    return redirect("admin_mark_submission_list")

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

    if (
        not request.user.is_superuser
        and submission.teacher != request.user.teacher_profile
    ):
        messages.error(
            request,
            "You cannot edit another teacher's draft."
        )
        return redirect("teacher_draft_submissions")

    marks = Mark.objects.filter(
        submission=submission
    ).select_related("student")

    if request.method == "POST":

        for mark in marks:

            value = request.POST.get(f"mark_{mark.id}")

        if value:

            mark.marks = float(value)
            mark.grade = calculate_grade(mark.marks)
            mark.save()

    messages.success(
        request,
        "Draft updated successfully."
    )

    return redirect(
        "teacher_draft_submissions"
    )

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

    school = SchoolProfile.objects.first()

    student = get_object_or_404(Student, id=id)

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

    school = SchoolProfile.objects.first()

    student = get_object_or_404(Student, id=id)

    marks = Mark.objects.filter(student=student).select_related(
        "subject",
        "exam",
    )

    exam = marks.first().exam if marks.exists() else None

    total = sum(mark.marks for mark in marks)

    average = round(total / marks.count(), 2) if marks.exists() else 0
    # Calculate Position
    students = Student.objects.filter(
        school_class=student.school_class
    )

    results = []

    for s in students:

        if exam:
            student_marks = Mark.objects.filter(
                student=s,
                exam=exam,
            )
        else:
            student_marks = Mark.objects.filter(student=s)
        if student_marks.exists():
            average_marks = (
                sum(m.marks for m in student_marks)
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

    results.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    position = 1

    for index, item in enumerate(results, start=1):
        if item[0] == student.id:
            position = index
            break

    class_size = len(results)

    overall_grade = calculate_overall_grade(average)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
    buffer,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        topMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )
        

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    normal = styles["Normal"]
    normal.alignment = TA_CENTER

    italic = styles["Italic"]
    italic.alignment = TA_CENTER

    story = []

    # ==========================
    # School Logo
    # ==========================
   # ==========================
# Header (Logo + School Details)
# ==========================

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

    school_info = Paragraph(
        f"""
        <font size=16><b>{school.name}</b></font><br/>
        <font size=9>{school.motto or ""}</font><br/>
        <font size=9>{school.address}</font><br/>
        <font size=9>Tel: {school.phone}</font><br/>
        <font size=9>{school.email or ""}</font><br/>
        <font size=9>{school.current_term} | {school.academic_year}</font>
        """,
        styles["Normal"],
    )

    header = Table(
        [
            [logo, school_info]
        ],
        colWidths=[0.8*inch, 6.0*inch],
    )

    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("ALIGN", (0,0), (0,0), "LEFT"),
                ("ALIGN", (1,0), (1,0), "RIGHT"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 0.05*inch))
        

    
    student_info = [

        ["Admission No", student.admission_number],

        ["Student Name",
         f"{student.first_name} {student.last_name}"],

        ["Gender", student.gender],

        ["Class", str(student.school_class)],

        ["Date of Birth",
         str(student.date_of_birth)],

        ["Exam",
         str(exam) if exam else "N/A"],

    ]

    info_table = Table(
        student_info,
        colWidths=[2 * inch, 4 * inch],
    )

    info_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),

                ("BACKGROUND", (0, 0), (0, -1), HexColor("#D9EAD3")),

                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    # Student Photo
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

    # Combine Student Info and Photo
    # ======================================================
# STUDENT DETAILS + PHOTO
# ======================================================

    details = Table(
        [
            [
                info_table,
                photo,
            ]
        ],
        colWidths=[5.1 * inch, 1.7 * inch],
    )

    details.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

# ======================================================
# MARKS TABLE
# ======================================================

    data = [
        [
            "No",
            "Subject",
            "Marks",
            "Grade",
        ]
    ]

    for index, mark in enumerate(marks, start=1):

        data.append(
            [
                index,
                mark.subject.name,
                mark.marks,
                mark.grade,
            ]
        )

# Summary rows
    data.append(["", "", "", ""])

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

    results = Table(
        data,
        colWidths=[
            0.7 * inch,
            3.8 * inch,
            0.8 * inch,
            0.8 * inch,
        ],
    )

    results.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),

                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),

                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),

                ("BACKGROUND", (0, -3), (-1, -3), colors.lightgrey),
                ("BACKGROUND", (0, -2), (-1, -2), HexColor("#D9EAD3")),
                ("BACKGROUND", (0, -1), (-1, -1), HexColor("#FFF2CC")),

                ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, -3), (1, -1), "LEFT"),
                ("FONTNAME", (1, -3), (1, -1), "Helvetica-Bold"),
            ]
        )
    )

# ======================================================
# MAIN CONTAINER (Keeps both tables aligned)
# ======================================================

    main_table = Table(
        [
            [details],
            [results],
        ],
        colWidths=[6.8 * inch],
    )

    main_table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )

    story.append(main_table)

    story.append(Spacer(1, 0.08 * inch))

   # ==========================
# Teacher's Remark
# ==========================

    if average >= 80:
        teacher_remark = "Excellent Performance. Keep it up."
    elif average >= 70:
        teacher_remark = "Very Good Performance."
    elif average >= 60:
        teacher_remark = "Good Work. Keep Improving."
    elif average >= 50:
        teacher_remark = "Fair Performance."
    else:
        teacher_remark = "Needs More Effort."

# ==========================
# Principal's Remark
# ==========================

    if average >= 80:
        principal_remark = "Excellent performance. Keep up the outstanding work."
    elif average >= 70:
        principal_remark = "Very good performance. Continue working hard."
    elif average >= 60:
        principal_remark = "Good performance. Aim even higher next term."
    elif average >= 50:
        principal_remark = "Fair performance. More effort will lead to better results."
    else:
        principal_remark = "Needs improvement. Work harder and remain focused."
    story.append(
    Spacer(1, 0.10 * inch)
)

    story.append(
        Paragraph(
            "<font size='8' color='grey'><i>"
            "Generated by School Management System"
            "</i></font>",
            styles["Normal"],
        )
    )

# ==========================
# Fee Summary
# ==========================

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
        ["Total Fee", f"KSh {total_fee}"],
        ["Amount Paid", f"KSh {total_paid}"],
        ["Balance", f"KSh {balance}"],
    ]

    fee_table = Table(
        fee_data,
        colWidths=[2.5 * inch, 2 * inch],
    )

    fee_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#dff0d8")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(fee_table)
    story.append(Spacer(1, 0.12 * inch))

# ==========================
# Teacher & Principal Remarks
# ==========================

    remarks_table = Table(
        [
            [
                Paragraph("<b>Teacher's Remarks</b>", styles["Heading3"]),
                Paragraph("<b>Principal's Remarks</b>", styles["Heading3"]),
            ],
            [
                Paragraph(teacher_remark, styles["Normal"]),
                Paragraph(principal_remark, styles["Normal"]),
            ],
        ],
        colWidths=[3.3 * inch, 3.3 * inch],
    )

    remarks_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(remarks_table)

    story.append(Spacer(1, 0.15 * inch))

# ==========================
# Signature Section
# ==========================

    signature_content = []

    if school and school.principal_signature:
        try:
            signature = Image(
                school.principal_signature.path,
                width=120,
                height=50,
            )
            signature_content.append(signature)
        except Exception:
            signature_content.append("")
    else:
        signature_content.append("")

    signature_table = Table(
    [
        [
            "__________________________",
            signature_content[0],
        ],
        [
            "Class Teacher",
            school.principal_name or "Principal",
        ],
    ],
    colWidths=[3.3 * inch, 3.3 * inch],
)

    signature_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    story.append(signature_table)

    story.append(Spacer(1, 0.08 * inch))

    story.append(
        Paragraph(
            "Generated by School Management System",
            styles["Italic"],
        )
    )

    # Build PDF
    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=f"{student.admission_number}_Report.pdf",
        content_type="application/pdf",
    )

@login_required
@admin_or_bursar
def class_results(request):

    classes = SchoolClass.objects.all()
    exams = Exam.objects.all()

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
            id=request.POST["school_class"]
        )

        selected_exam = get_object_or_404(
            Exam,
            id=request.POST["exam"]
        )

        students = Student.objects.filter(
            school_class=selected_class
        )

        subjects = Subject.objects.all().order_by("name")

        # Student Results
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

        # Sort by Total
        results.sort(
            key=lambda x: x["total"],
            reverse=True
        )

        # Positions
        for i, row in enumerate(results, start=1):
            row["position"] = i

        # Summary
        student_count = len(results)

        if results:

            class_average = round(
                sum(r["average"] for r in results) / student_count,
                2
            )

            highest_total = results[0]["total"]
            lowest_total = results[-1]["total"]

        # Subject Analysis
        for subject in subjects:

            subject_marks = Mark.objects.filter(
                subject=subject,
                exam=selected_exam,
                student__school_class=selected_class
            )

            if subject_marks.exists():

                highest = subject_marks.order_by("-marks").first().marks
                lowest = subject_marks.order_by("marks").first().marks
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
