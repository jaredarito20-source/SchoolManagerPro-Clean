from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Avg, F
from reportlab.pdfgen import canvas
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.http import HttpResponse
from datetime import date
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponse
import uuid
from io import BytesIO
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from io import BytesIO
from django.http import FileResponse
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

from reportlab.pdfbase import pdfmetrics
from .models import (
    Student,
    Teacher,
    Subject,
    SchoolClass,
    Exam,
    Mark,
    SchoolProfile,
    FeeStructure,
    FeePayment,
    Attendance,
    Timetable,
    ExamTimetable,
    InventoryCategory,
    InventoryItem,
    StockTransaction,
    Book,
    BorrowBook,
    SalaryStructure,
    Payroll,
    Vehicle,
    TransportRoute,
    StudentTransport,
    Driver,
    HostelBlock,
    HostelRoom,
    StudentHostel,
    HostelWarden,
    HostelTransfer,
    HostelBed,
)
from .decorators import (
    admin_required,
    teacher_required,
    bursar_required,
    secretary_required,
    admin_or_teacher,
    admin_or_bursar,
    admin_teacher_secretary,
    in_group,
)
# ======================================
# User Role Checks
# ======================================

def draw_school_header(pdf, title):

    # School Name
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(HexColor("#003366"))
    pdf.drawCentredString(
        300,
        810,
        "YOUR SCHOOL NAME"
    )

    pdf.setFont("Helvetica", 11)

    pdf.setFillColor(HexColor("#000000"))

    pdf.drawCentredString(
        300,
        792,
        "P.O Box 12345 - Nairobi"
    )

    pdf.drawCentredString(
        300,
        777,
        "Phone: +254 700 000000"
    )

    pdf.drawCentredString(
        300,
        762,
        "Email: info@yourschool.ac.ke"
    )

    pdf.line(
        40,
        748,
        560,
        748,
    )

    pdf.setFont("Helvetica-Bold", 15)

    pdf.drawCentredString(
        300,
        728,
        title,
    )

    pdf.line(
        40,
        718,
        560,
        718,
    )

from datetime import datetime

def draw_school_footer(pdf, request):

    pdf.line(
        40,
        40,
        560,
        40,
    )

    pdf.setFont("Helvetica", 9)

    pdf.drawString(
        40,
        25,
        f"Printed By: {request.user.username}"
    )

    pdf.drawRightString(
        560,
        25,
        datetime.now().strftime(
            "%d-%m-%Y %H:%M"
        )
    )

def is_admin(user):
    return (
        user.is_superuser or
        user.groups.filter(name="Administrators").exists()
    )


def is_teacher(user):
    return user.groups.filter(name="Teachers").exists()


def is_bursar(user):
    return user.groups.filter(name="Bursars").exists()


def is_secretary(user):
    return user.groups.filter(name="Secretaries").exists()







@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Teachers",
    "Bursar",
    "Secretaries",
)
def home(request):
    ...

def home(request):
    school = SchoolProfile.objects.first()

    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = SchoolClass.objects.count()
    total_subjects = Subject.objects.count()

    total_payments = FeePayment.objects.aggregate(
        total=Sum("amount")
    )["total"] or 0

    total_balance = sum(
        student.balance() for student in Student.objects.all()
    )

    recent_students = Student.objects.order_by("-id")[:5]
    recent_payments = FeePayment.objects.order_by("-payment_date")[:5]

    context = {
        "school": school,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_payments": total_payments,
        "total_balance": total_balance,
        "recent_students": recent_students,
        "recent_payments": recent_payments,
    }

    return render(request, "students/home.html", context)
@login_required
@admin_teacher_secretary
def add_student(request):
    if request.method == "POST":
        school_class = None
        school_class_id = request.POST.get("school_class")

        if school_class_id:
            school_class = SchoolClass.objects.get(id=school_class_id)

        Student.objects.create(
            admission_number=request.POST["admission_number"],
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            gender=request.POST["gender"],
            date_of_birth=request.POST["date_of_birth"],
            school_class=school_class,
            parent_name=request.POST["parent_name"],
            phone=request.POST["phone"],
            photo=request.FILES.get("photo"),
        )

        return redirect("student_list")

    classes = SchoolClass.objects.all()

    return render(request, "students/add_student.html", {
        "classes": classes
    })

@login_required
@admin_teacher_secretary
def student_list(request):
    students = Student.objects.all()
    return render(request, "students/student_list.html", {
        "students": students
    })

@login_required
@admin_teacher_secretary
def edit_student(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == "POST":
        school_class = None
        school_class_id = request.POST.get("school_class")

        if school_class_id:
            school_class = SchoolClass.objects.get(id=school_class_id)

        student.admission_number = request.POST["admission_number"]
        student.first_name = request.POST["first_name"]
        student.last_name = request.POST["last_name"]
        student.gender = request.POST["gender"]
        student.date_of_birth = request.POST["date_of_birth"]
        student.school_class = school_class
        student.parent_name = request.POST["parent_name"]
        student.phone = request.POST["phone"]

        student.save()

        return redirect("student_list")

    classes = SchoolClass.objects.all()

    return render(request, "students/edit_student.html", {
        "student": student,
        "classes": classes,
    })



@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    
)
def promotion_list(request):
    classes = SchoolClass.objects.all().order_by("name")

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

    if request.method == "POST":

        from_class = get_object_or_404(
            SchoolClass,
            id=request.POST["from_class"]
        )

        to_class = get_object_or_404(
            SchoolClass,
            id=request.POST["to_class"]
        )

        students = Student.objects.filter(
            school_class=from_class
        )

        count = students.update(
            school_class=to_class
        )

        messages.success(
            request,
            f"{count} students promoted from {from_class} to {to_class}."
        )

        return redirect("promotion_list")

    return redirect("promotion_list")


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == "POST":
        student.delete()
        return redirect("student_list")

    return render(request, "students/delete_student.html", {
        "student": student
    })


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, "students/teacher_list.html", {
        "teachers": teachers
    })


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def add_teacher(request):
    if request.method == "POST":
        Teacher.objects.create(
            employee_number=request.POST["employee_number"],
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            gender=request.POST["gender"],
            phone=request.POST["phone"],
            email=request.POST["email"],
            subject=request.POST["subject"],
        )

        return redirect("teacher_list")

    return render(request, "students/add_teacher.html")


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)

    if request.method == "POST":
        teacher.employee_number = request.POST["employee_number"]
        teacher.first_name = request.POST["first_name"]
        teacher.last_name = request.POST["last_name"]
        teacher.gender = request.POST["gender"]
        teacher.phone = request.POST["phone"]
        teacher.email = request.POST["email"]
        teacher.subject = request.POST["subject"]
        teacher.save()

        return redirect("teacher_list")

    return render(request, "students/edit_teacher.html", {
        "teacher": teacher
    })


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)

    if request.method == "POST":
        teacher.delete()
        return redirect("teacher_list")

    return render(request, "students/delete_teacher.html", {
        "teacher": teacher
    })


@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "students/subject_list.html", {
        "subjects": subjects
    })



@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def add_subject(request):
    if request.method == "POST":
        teacher = None
        teacher_id = request.POST.get("teacher")
        if teacher_id:
            teacher = Teacher.objects.get(id=teacher_id)

        Subject.objects.create(
            name=request.POST["name"],
            code=request.POST["code"],
            teacher=teacher,
        )

        return redirect("subject_list")

    teachers = Teacher.objects.all()
    return render(request, "students/add_subject.html", {
        "teachers": teachers
    })


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def edit_subject(request, id):
    subject = get_object_or_404(Subject, id=id)

    if request.method == "POST":
        teacher = None
        teacher_id = request.POST.get("teacher")
        if teacher_id:
            teacher = Teacher.objects.get(id=teacher_id)

        subject.name = request.POST["name"]
        subject.code = request.POST["code"]
        subject.teacher = teacher
        subject.save()

        return redirect("subject_list")

    teachers = Teacher.objects.all()
    return render(request, "students/edit_subject.html", {
        "subject": subject,
        "teachers": teachers,
    })



@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_subject(request, id):
    subject = get_object_or_404(Subject, id=id)

    if request.method == "POST":
        subject.delete()
        return redirect("subject_list")

    return render(request, "students/delete_subject.html", {
        "subject": subject
    })


@login_required
@admin_required
def class_list(request):
    classes = SchoolClass.objects.all()
    return render(request, "students/class_list.html", {
        "classes": classes
    })

@login_required
@admin_required
def add_class(request):
    if request.method == "POST":
        teacher = None
        teacher_id = request.POST.get("class_teacher")

        if teacher_id:
            teacher = Teacher.objects.get(id=teacher_id)

        SchoolClass.objects.create(
            name=request.POST["name"],
            class_teacher=teacher,
        )

        return redirect("class_list")

    teachers = Teacher.objects.all()
    return render(request, "students/add_class.html", {
        "teachers": teachers
    })


@login_required
@admin_required
def edit_class(request, id):
    school_class = get_object_or_404(SchoolClass, id=id)

    if request.method == "POST":
        teacher = None
        teacher_id = request.POST.get("class_teacher")

        if teacher_id:
            teacher = Teacher.objects.get(id=teacher_id)

        school_class.name = request.POST["name"]
        school_class.class_teacher = teacher
        school_class.save()

        return redirect("class_list")

    teachers = Teacher.objects.all()
    return render(request, "students/edit_class.html", {
        "school_class": school_class,
        "teachers": teachers,
    })


@login_required
@admin_required
def delete_class(request, id):
    school_class = get_object_or_404(SchoolClass, id=id)

    if request.method == "POST":
        school_class.delete()
        return redirect("class_list")

    return render(request, "students/delete_class.html", {
        "school_class": school_class
    })

# ==========================
# Exams
# ==========================
@login_required
def exam_list(request):
    exams = Exam.objects.all()

    return render(request, "students/exam_list.html", {
        "exams": exams
    })


@login_required
@user_passes_test(is_admin)
def add_exam(request):
    if request.method == "POST":
        Exam.objects.create(
            name=request.POST["name"],
            term=request.POST["term"],
            year=request.POST["year"],
        )

        return redirect("exam_list")

    return render(request, "students/add_exam.html")


@login_required
@user_passes_test(is_admin)
def edit_exam(request, id):
    exam = get_object_or_404(Exam, id=id)

    if request.method == "POST":
        exam.name = request.POST["name"]
        exam.term = request.POST["term"]
        exam.year = request.POST["year"]
        exam.save()

        return redirect("exam_list")

    return render(request, "students/edit_exam.html", {
        "exam": exam
    })


@login_required
@user_passes_test(is_admin)
def delete_exam(request, id):
    exam = get_object_or_404(Exam, id=id)

    if request.method == "POST":
        exam.delete()
        return redirect("exam_list")

    return render(request, "students/delete_exam.html", {
        "exam": exam
    })
# ==========================
# Marks
# ==========================
@login_required
@admin_or_teacher
def mark_list(request):
    marks = Mark.objects.all()

    return render(request, "students/mark_list.html", {
        "marks": marks
    })


@login_required
@admin_or_teacher
def add_mark(request):

    classes = SchoolClass.objects.all()
    subjects = Subject.objects.all()
    exams = Exam.objects.all()

    students = Student.objects.none()
    selected_class = None

    if request.method == "POST":

        class_id = request.POST.get("school_class")

        if class_id:
            selected_class = get_object_or_404(SchoolClass, id=class_id)
            students = Student.objects.filter(school_class=selected_class)

        # If only selecting the class, reload the page
        if "student" not in request.POST or request.POST.get("student") == "":
            return render(request, "students/add_mark.html", {
                "classes": classes,
                "students": students,
                "subjects": subjects,
                "exams": exams,
                "selected_class": selected_class,
            })

        student = get_object_or_404(Student, id=request.POST["student"])
        subject = get_object_or_404(Subject, id=request.POST["subject"])
        exam = get_object_or_404(Exam, id=request.POST["exam"])
        marks = float(request.POST["marks"])

        if Mark.objects.filter(
            student=student,
            subject=subject,
            exam=exam,
        ).exists():

            return render(request, "students/add_mark.html", {
                "classes": classes,
                "students": students,
                "subjects": subjects,
                "exams": exams,
                "selected_class": selected_class,
                "error": "Marks for this student, subject and exam already exist.",
            })

        Mark.objects.create(
            student=student,
            subject=subject,
            exam=exam,
            marks=marks,
            grade=calculate_grade(marks),
        )

        return redirect("mark_list")

    return render(request, "students/add_mark.html", {
        "classes": classes,
        "students": students,
        "subjects": subjects,
        "exams": exams,
        "selected_class": selected_class,
    })
@login_required
@admin_or_teacher
def edit_mark(request, id):
    mark = get_object_or_404(Mark, id=id)

    if request.method == "POST":
        mark.student = Student.objects.get(id=request.POST["student"])
        mark.subject = Subject.objects.get(id=request.POST["subject"])
        mark.exam = Exam.objects.get(id=request.POST["exam"])
        mark.marks = float(request.POST["marks"])
        mark.grade = calculate_grade(mark.marks)
        mark.save()

        return redirect("mark_list")

    return render(request, "students/edit_mark.html", {
        "mark": mark,
        "students": Student.objects.all(),
        "subjects": Subject.objects.all(),
        "exams": Exam.objects.all(),
    })


@login_required
@admin_or_teacher
def delete_mark(request, id):
    mark = get_object_or_404(Mark, id=id)

    if request.method == "POST":
        mark.delete()
        return redirect("mark_list")

    return render(request, "students/delete_mark.html", {
        "mark": mark

    })


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
# ==========================
# FEE STRUCTURE
# ==========================




@login_required
@admin_or_bursar
@in_group("Administrators", "Head Teacher", "Bursar")
def finance_dashboard(request):

    # Total expected fees
    total_expected = 0

    students = Student.objects.select_related("school_class")

    for student in students:

        structure = FeeStructure.objects.filter(
            school_class=student.school_class
        ).first()

        if structure:
            total_expected += (
                structure.tuition_fee
                + structure.activity_fee
                + structure.exam_fee
                + structure.other_fee
            )

    # Total collected
    total_collected = (
        FeePayment.objects.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # Outstanding balance
    outstanding = total_expected - total_collected

    # Today's collections
    today_collection = (
        FeePayment.objects.filter(
            payment_date=date.today()
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # Number of payments
    total_payments = FeePayment.objects.count()

    return render(
        request,
        "fees/finance_dashboard.html",
        {
            "total_expected": total_expected,
            "total_collected": total_collected,
            "outstanding": outstanding,
            "today_collection": today_collection,
            "total_payments": total_payments,
        },
    )
@login_required
@admin_or_bursar
@in_group("Bursar")
def fee_structure_list(request):
    fees = FeeStructure.objects.all()

    return render(
        request,
        "students/fee_structure_list.html",
        {"fees": fees},
    )

@login_required
@admin_or_bursar
@in_group("Administrators", "Bursar")
def print_receipt(request, id):

    payment = get_object_or_404(
        FeePayment,
        id=id
    )

    school = SchoolProfile.objects.first()

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

        if school.address:
            story.append(
                Paragraph(
                    school.address,
                    styles["Normal"],
                )
            )

        if school.phone:
            story.append(
                Paragraph(
                    f"Phone: {school.phone}",
                    styles["Normal"],
                )
            )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>OFFICIAL SCHOOL FEE RECEIPT</b>",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 15))

    data = [

        ["Receipt No", payment.receipt_number],

        [
            "Student",
            f"{payment.student.first_name} {payment.student.last_name}",
        ],

        [
            "Admission No",
            payment.student.admission_number,
        ],

        [
            "Class",
            payment.student.school_class.name,
        ],

        [
            "Amount Paid",
            f"KSh {payment.amount}",
        ],

        [
            "Payment Method",
            payment.payment_method,
        ],

        [
            "Reference",
            payment.reference,
        ],

        [
            "Payment Date",
            str(payment.payment_date),
        ],

        [
            "Recorded By",
            payment.recorded_by.username
            if payment.recorded_by
            else "",
        ],

    ]

    table = Table(
        data,
        colWidths=[170, 300],
    )

    table.setStyle(
        TableStyle([

            ("GRID", (0,0), (-1,-1), 1, colors.black),

            ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),

            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),

            ("BOTTOMPADDING", (0,0), (-1,-1), 8),

            ("TOPPADDING", (0,0), (-1,-1), 8),

        ])
    )

    story.append(table)

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            "Thank you for your payment.",
            styles["Heading3"],
        )
    )

    story.append(Spacer(1, 40))

    story.append(
        Paragraph(
            "__________________________",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "Bursar Signature",
            styles["Normal"],
        )
    )

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="Receipt.pdf",
    )


@login_required
@admin_or_bursar
@in_group("Bursar")
def add_fee_structure(request):

    if request.method == "POST":

        school_class = SchoolClass.objects.get(
            id=request.POST["school_class"]
        )

        FeeStructure.objects.create(
            school_class=school_class,
            tuition_fee=request.POST["tuition_fee"],
            activity_fee=request.POST["activity_fee"],
            exam_fee=request.POST["exam_fee"],
            other_fee=request.POST["other_fee"],
        )

        return redirect("fee_structure_list")

    classes = SchoolClass.objects.all()

    return render(
        request,
        "students/add_fee_structure.html",
        {"classes": classes},
    )


# ==========================
# FEE PAYMENTS
# ==========================
@login_required
@admin_or_bursar
@in_group("Administrators", "Bursar")
def fee_payment_list(request):

    payments = FeePayment.objects.select_related(
        "student",
        "student__school_class",
    ).order_by("-payment_date", "-id")

    return render(
        request,
        "students/fee_payment_list.html",
        {
            "payments": payments,
        },
    )





@login_required
@admin_or_bursar
@in_group("Administrators", "Head Teacher", "Bursar")
def print_fee_statement(request, id):

    student = Student.objects.get(id=id)

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("payment_date")

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    if fee_structure:
        total_fees = (
            fee_structure.tuition_fee
            + fee_structure.activity_fee
            + fee_structure.exam_fee
            + fee_structure.other_fee
        )
    else:
        total_fees = 0

    total_paid = payments.aggregate(
        total=Sum("amount")
    )["total"] or 0

    balance = total_fees - total_paid

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Fee Statement")

    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(170, y, "STUDENT FEE STATEMENT")

    y -= 40

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, y, f"Student: {student.first_name} {student.last_name}")
    y -= 20

    pdf.drawString(50, y, f"Admission No: {student.admission_number}")
    y -= 20

    pdf.drawString(50, y, f"Class: {student.school_class.name}")

    y -= 40

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(50, y, f"Total Fees : KSh {total_fees}")
    y -= 20

    pdf.drawString(50, y, f"Total Paid : KSh {total_paid}")
    y -= 20

    pdf.drawString(50, y, f"Balance    : KSh {balance}")

    y -= 40

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(50, y, "PAYMENT HISTORY")

    y -= 25

    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, y, "Date")
    pdf.drawString(140, y, "Receipt")
    pdf.drawString(280, y, "Method")
    pdf.drawString(430, y, "Amount")

    y -= 20

    for payment in payments:

        pdf.drawString(
            50,
            y,
            payment.payment_date.strftime("%d-%m-%Y"),
        )

        pdf.drawString(
            140,
            y,
            payment.receipt_number,
        )

        pdf.drawString(
            280,
            y,
            payment.payment_method,
        )

        pdf.drawString(
            430,
            y,
            f"KSh {payment.amount}",
        )

        y -= 20

        if y < 60:
            pdf.showPage()
            y = 800

    pdf.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="fee_statement.pdf",
    )

@login_required
@admin_or_bursar
@in_group(
    "Administrators",
    "Head Teacher",
    "Bursar",
)
def fee_statement(request, id):

    student = get_object_or_404(Student, id=id)

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("-payment_date")

    # Get the student's fee structure
    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    if fee_structure:
        total_fees = (
            fee_structure.tuition_fee
            + fee_structure.activity_fee
            + fee_structure.exam_fee
            + fee_structure.other_fee
        )
    else:
        total_fees = 0

    total_paid = (
        payments.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    balance = total_fees - total_paid

    return render(
        request,
        "fees/fee_statement.html",
        {
            "student": student,
            "payments": payments,
            "total_fees": total_fees,
            "total_paid": total_paid,
            "balance": balance,
        },
    )
@login_required
@admin_or_bursar
@in_group("Bursar")
def fee_balance_list(request):
    students = Student.objects.select_related("school_class").all()

    return render(
        request,
        "fees/fee_balance_list.html",
        {"students": students},
    )
@login_required
@admin_or_bursar
def edit_payment(request, id):

    payment = FeePayment.objects.get(id=id)
    students = Student.objects.all()

    if request.method == "POST":

        payment.student = Student.objects.get(
            id=request.POST["student"]
        )

        payment.amount_paid = request.POST["amount_paid"]
        payment.payment_date = request.POST["payment_date"]
        payment.payment_method = request.POST["payment_method"]
        payment.receipt_number = request.POST["receipt_number"]

        payment.save()

        return redirect("fee_payment_list")

    return render(
        request,
        "students/edit_payment.html",
        {
            "payment": payment,
            "students": students,
        },
    )
@login_required
@admin_or_bursar
def delete_payment(request, id):

    payment = FeePayment.objects.get(id=id)

    if request.method == "POST":
        payment.delete()
        return redirect("fee_payment_list")

    return render(
        request,
        "students/delete_payment.html",
        {
            "payment": payment,
        },
    )

@login_required
@admin_or_bursar
@in_group("Administrators", "Bursar")
def add_fee_payment(request):

    students = Student.objects.select_related(
        "school_class"
    ).order_by(
        "admission_number"
    )

    if request.method == "POST":

        FeePayment.objects.create(

            student=Student.objects.get(
                id=request.POST["student"]
            ),

            amount=request.POST["amount"],

            payment_date=request.POST["payment_date"],

            payment_method=request.POST["payment_method"],

            receipt_number="RCPT-" + uuid.uuid4().hex[:8].upper(),

            reference=request.POST["reference"],

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Fee payment recorded successfully."
        )

        return redirect("fee_payment_list")

    return render(
    request,
    "students/add_fee_payment.html",
    {
        "students": students,
        "today": date.today(),
    },
)

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def salary_structure_list(request):

    salaries = SalaryStructure.objects.select_related(
        "teacher"
    ).all()

    return render(
        request,
        "students/salary_structure_list.html",
        {
            "salaries": salaries,
        },
    )
@login_required
@admin_or_bursar
def add_salary_structure(request):

    teachers = Teacher.objects.all()

    if request.method == "POST":

        SalaryStructure.objects.create(
            teacher=Teacher.objects.get(id=request.POST["teacher"]),
            basic_salary=request.POST["basic_salary"],
            house_allowance=request.POST["house_allowance"],
            medical_allowance=request.POST["medical_allowance"],
            transport_allowance=request.POST["transport_allowance"],
            other_allowance=request.POST["other_allowance"],
            paye=request.POST["paye"],
            sha=request.POST["sha"],
            nssf=request.POST["nssf"],
            other_deductions=request.POST.get("other_deductions", 0),
            bank_name=request.POST.get("bank_name", ""),
            account_number=request.POST.get("account_number", ""),
        )
        return redirect("salary_structure_list")

    return render(
        request,
        "students/add_salary_structure.html",
        {
            "teachers": teachers,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def edit_salary_structure(request, id):

    salary = get_object_or_404(SalaryStructure, id=id)

    if request.method == "POST":

        salary.teacher = Teacher.objects.get(
            id=request.POST["teacher"]
        )

        salary.basic_salary = request.POST["basic_salary"]
        salary.house_allowance = request.POST["house_allowance"]
        salary.transport_allowance = request.POST["transport_allowance"]
        salary.medical_allowance = request.POST["medical_allowance"]
        salary.other_allowance = request.POST["other_allowance"]

        salary.nssf = request.POST["nssf"]
        salary.sha = request.POST["sha"]
        salary.paye = request.POST["paye"]
        salary.other_deductions = request.POST["other_deductions"]

        salary.save()

        return redirect("salary_structure_list")

    teachers = Teacher.objects.all()

    return render(
        request,
        "students/edit_salary_structure.html",
        {
            "salary": salary,
            "teachers": teachers,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def delete_salary_structure(request, id):

    salary = get_object_or_404(
        SalaryStructure,
        id=id,
    )

    if request.method == "POST":

        salary.delete()

        return redirect(
            "salary_structure_list"
        )

    return render(
        request,
        "students/delete_salary_structure.html",
        {
            "salary": salary,
        },
    )

@login_required
@admin_or_bursar
def generate_payroll(request):

    if request.method == "POST":

        month = request.POST["month"]
        year = int(request.POST["year"])

        salary_structures = SalaryStructure.objects.select_related(
            "teacher"
        )

        for salary in salary_structures:

            if Payroll.objects.filter(
                teacher=salary.teacher,
                month=month,
                year=year,
            ).exists():
                continue

            gross_salary = salary.gross_salary()

            deductions = (
                salary.paye
                + salary.sha
                + salary.nssf
                + salary.other_deductions
            )

            net_salary = gross_salary - deductions

            Payroll.objects.create(
                teacher=salary.teacher,
                month=month,
                year=year,
                basic_salary=salary.basic_salary,
                gross_salary=gross_salary,
                paye=salary.paye,
                sha=salary.sha,
                nssf=salary.nssf,
                other_deductions=salary.other_deductions,
                deductions=deductions,
                net_salary=net_salary,
            )

        return redirect("payroll_list")

    return render(
        request,
        "students/generate_payroll.html",
    )

@login_required
@admin_or_bursar
def payroll_list(request):

    payrolls = Payroll.objects.select_related(
        "teacher"
    ).order_by(
        "-year",
        "-generated_on",
        "teacher__first_name",
    )

    return render(
        request,
        "students/payroll_list.html",
        {
            "payrolls": payrolls,
        },
    )

@login_required
@admin_or_bursar
def print_payslip(request, id):

    payroll = get_object_or_404(Payroll, id=id)
    school = SchoolProfile.objects.first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    story = []

    # School Header
    if school:

        story.append(
            Paragraph(
                f"<font size='18'><b>{school.name}</b></font>",
                styles["Title"],
            )
        )

        story.append(
            Paragraph(
                f"{school.address}<br/>"
                f"Tel: {school.phone}<br/>"
                f"Email: {school.email}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "<b>EMPLOYEE PAYSLIP</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    # Employee Details

    teacher = payroll.teacher

    employee_table = Table(
        [
            ["Employee", str(teacher)],
            ["Month", payroll.month],
            ["Year", payroll.year],
            ["Date Generated", payroll.generated_on],
        ],
        colWidths=[2.2 * inch, 4.2 * inch],
    )

    employee_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(employee_table)

    story.append(Spacer(1, 0.2 * inch))

    # Salary Breakdown

    salary_table = Table(
        [
            ["Description", "Amount (KSh)"],

            ["Basic Salary", payroll.basic_salary],
            ["Gross Salary", payroll.gross_salary],

            ["PAYE", payroll.paye],
            ["SHA", payroll.sha],
            ["NSSF", payroll.nssf],
            ["Other Deductions", payroll.other_deductions],

            ["Total Deductions", payroll.deductions],

            ["NET SALARY", payroll.net_salary],
        ],
        colWidths=[4.5 * inch, 2 * inch],
    )

    salary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0,0), (-1,-1), 1, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),

                ("BACKGROUND", (0,-1), (-1,-1), colors.lightgreen),

                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),

                ("ALIGN", (1,1), (-1,-1), "RIGHT"),
            ]
        )
    )

    story.append(salary_table)

    story.append(Spacer(1, 0.4 * inch))

    # Signature Section

    signature_table = Table(
        [
            [
                "_______________________",
                "_______________________",
            ],
            [
                "Employee Signature",
                "Bursar / Principal",
            ],
        ],
        colWidths=[3.3 * inch, 3.3 * inch],
    )

    signature_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("TOPPADDING", (0,0), (-1,-1), 10),
            ]
        )
    )

    story.append(signature_table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=f"{teacher}_Payslip.pdf",
    )

@login_required
@admin_or_bursar
def print_salary_structure(request, id):

    salary = get_object_or_404(SalaryStructure, id=id)
    school = SchoolProfile.objects.first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    story = []

    # School Header
    if school:

        story.append(
            Paragraph(
                f"<font size='18'><b>{school.name}</b></font>",
                styles["Title"],
            )
        )

        story.append(
            Paragraph(
                f"{school.address}<br/>"
                f"Tel: {school.phone}<br/>"
                f"Email: {school.email}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "<b>SALARY STRUCTURE</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    # Teacher Details

    teacher_table = Table(
        [
            ["Teacher", str(salary.teacher)],
            ["Bank", salary.bank_name or "-"],
            ["Account Number", salary.account_number or "-"],
        ],
        colWidths=[2.2 * inch, 4.2 * inch],
    )

    teacher_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(teacher_table)

    story.append(Spacer(1, 0.2 * inch))

    # Salary Breakdown

    salary_table = Table(
        [
            ["Description", "Amount (KSh)"],

            ["Basic Salary", salary.basic_salary],
            ["House Allowance", salary.house_allowance],
            ["Transport Allowance", salary.transport_allowance],
            ["Medical Allowance", salary.medical_allowance],
            ["Other Allowance", salary.other_allowance],

            ["Gross Salary", salary.gross_salary()],

            ["PAYE", salary.paye],
            ["SHA", salary.sha],
            ["NSSF", salary.nssf],
            ["Other Deductions", salary.other_deductions],

            ["Total Deductions", salary.total_deductions()],

            ["NET SALARY", salary.net_salary()],
        ],
        colWidths=[4.5 * inch, 2 * inch],
    )

    salary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgreen),

                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )

    story.append(salary_table)

    story.append(Spacer(1, 0.35 * inch))

    # Signature Section

    signature_table = Table(
        [
            [
                "______________________",
                "______________________",
            ],
            [
                "Teacher",
                school.principal_name if school else "Principal",
            ],
            [
                "",
                "Principal",
            ],
        ],
        colWidths=[3.3 * inch, 3.3 * inch],
    )

    signature_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(signature_table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=f"{salary.teacher}_Salary_Structure.pdf",
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

    attendances = Attendance.objects.select_related(
        "student",
        "school_class",
    )

    classes = SchoolClass.objects.all()

    school_class = request.GET.get("school_class")
    date = request.GET.get("date")

    if school_class:
        attendances = attendances.filter(
            school_class_id=school_class
        )

    if date:
        attendances = attendances.filter(
            date=date
        )

    attendances = attendances.order_by(
        "-date",
        "school_class__name",
        "student__admission_number",
    )

    return render(
        request,
        "students/attendance_list.html",
        {
            "attendances": attendances,
            "classes": classes,
        },
    )
@login_required
@admin_teacher_secretary
def add_attendance(request):

    if request.method == "POST":

        student = Student.objects.get(id=request.POST["student"])
        school_class = SchoolClass.objects.get(id=request.POST["school_class"])

        Attendance.objects.create(
            student=student,
            school_class=school_class,
            date=request.POST["date"],
            status=request.POST["status"],
        )

        return redirect("attendance_list")

    students = Student.objects.all()
    classes = SchoolClass.objects.all()

    return render(
        request,
        "students/add_attendance.html",
        {
            "students": students,
            "classes": classes,
            "today": date.today(),
        },
    )


from datetime import date

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
    "Secretarires",
)
def take_attendance(request):

    classes = SchoolClass.objects.all()

    students = None
    selected_class = None
    selected_date = date.today()

    # -------------------------
    # LOAD STUDENTS
    # -------------------------
    if request.method == "GET":

        class_id = request.GET.get("school_class")

        if class_id:

            selected_class = SchoolClass.objects.get(
                id=class_id
            )

            students = Student.objects.filter(
                school_class=selected_class
            ).order_by(
                "admission_number"
            )

            if request.GET.get("date"):
                selected_date = request.GET.get("date")

    # -------------------------
    # SAVE ATTENDANCE
    # -------------------------
    elif request.method == "POST":

        class_id = request.POST.get("school_class")

        selected_class = SchoolClass.objects.get(
            id=class_id
        )

        selected_date = request.POST.get("date")

        students = Student.objects.filter(
            school_class=selected_class
        )

        for student in students:

            status = request.POST.get(
                f"status_{student.id}"
            )

            remarks = request.POST.get(
                f"remarks_{student.id}"
            )

            Attendance.objects.update_or_create(

                student=student,
                date=selected_date,

                defaults={
                    "school_class": selected_class,
                    "status": status,
                    "remarks": remarks,
                }

            )

        messages.success(
            request,
            "Attendance saved successfully."
        )

        return redirect("take_attendance")

    return render(
        request,
        "students/take_attendance.html",
        {
            "classes": classes,
            "students": students,
            "selected_class": selected_class,
            "selected_date": selected_date,
            "today": date.today(),
        },
    )
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def edit_attendance(request, id):

    attendance = get_object_or_404(
        Attendance,
        id=id
    )

    if request.method == "POST":

        attendance.status = request.POST["status"]

        attendance.remarks = request.POST["remarks"]

        attendance.save()

        messages.success(
            request,
            "Attendance updated successfully."
        )

        return redirect("attendance_list")

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

    attendance = get_object_or_404(
        Attendance,
        id=id
    )

    if request.method == "POST":

        attendance.delete()

        messages.success(
            request,
            "Attendance deleted successfully."
        )

        return redirect("attendance_list")

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

    attendances = Attendance.objects.select_related(
        "student",
        "school_class",
    )

    school_class = request.GET.get("school_class")
    date = request.GET.get("date")

    if school_class:
        attendances = attendances.filter(
            school_class_id=school_class
        )

    if date:
        attendances = attendances.filter(
            date=date
        )

    attendances = attendances.order_by(
        "-date",
        "school_class__name",
        "student__admission_number",
    )

    return render(
    request,
    "students/attendance_print.html",
    {
        "attendances": attendances,
        "school_class": school_class,
        "date": date,
    },
)

# ==========================
# TIMETABLE
# ==========================
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
@admin_required
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
@admin_required
def add_user(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        group_name = request.POST["group"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")

            return redirect("add_user")

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        if group_name != "Administrator":
            group = Group.objects.get(name=group_name)
            user.groups.add(group)

        messages.success(request, "User created successfully.")

        return redirect("user_list")

    groups = Group.objects.all()

    return render(
        request,
        "students/add_user.html",
        {
            "groups": groups,
        },
    )


@login_required
@admin_required
def edit_user(request, id):
    return HttpResponse(f"Edit User {id}")


@login_required
@admin_required
def delete_user(request, id):
    return HttpResponse(f"Delete User {id}")


@login_required
@user_passes_test(is_admin)
def add_user(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        group_name = request.POST["group"]

        user = User.objects.create_user(
            username=username,
            password=password,
        )

        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        messages.success(request, "User created successfully.")

        return redirect("user_list")

    groups = Group.objects.all()

    return render(
        request,
        "students/add_user.html",
        {
            "groups": groups,
        },
    )

@login_required
@user_passes_test(is_admin)
def edit_user(request, id):
    user = get_object_or_404(User, id=id)

    if request.method == "POST":
        user.username = request.POST["username"]

        group_name = request.POST["group"]

        # Remove old groups
        user.groups.clear()

        # Add new group
        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        user.save()

        messages.success(request, "User updated successfully.")

        return redirect("user_list")

    groups = Group.objects.all()

    return render(
        request,
        "students/edit_user.html",
        {
            "user_obj": user,
            "groups": groups,
        },
    )


@login_required
@user_passes_test(is_admin)
def edit_user(request, id):

    user = get_object_or_404(User, id=id)

    if request.method == "POST":

        user.username = request.POST["username"]
        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.email = request.POST["email"]

        # Change password only if entered
        password = request.POST.get("password")
        if password:
            user.password = make_password(password)

        # Remove old groups
        user.groups.clear()

        # Assign new group
        group = Group.objects.get(name=request.POST["group"])
        user.groups.add(group)

        user.save()

        messages.success(request, "User updated successfully.")

        return redirect("user_list")

    groups = Group.objects.all()

    return render(
        request,
        "students/edit_user.html",
        {
            "user_obj": user,
            "groups": groups,
        },
    )

@login_required
@user_passes_test(is_admin)
def delete_user(request, id):

    user = get_object_or_404(User, id=id)

    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user_list")

    if request.method == "POST":
        user.delete()

        messages.success(
            request,
            "User deleted successfully."
        )

        return redirect("user_list")

    return render(
        request,
        "students/delete_user.html",
        {
            "user_obj": user,
        },
    )

@login_required
@admin_or_bursar
def print_receipt(request, id):

    payment = get_object_or_404(FeePayment, id=id)
    school = SchoolProfile.objects.first()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Receipt_{payment.receipt_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    elements = []

    # School Name
    elements.append(
        Paragraph(
            f"<font size='18'><b>{school.name}</b></font>",
            styles["Title"],
        )
    )

    elements.append(
        Paragraph(
            school.address,
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"Phone: {school.phone}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"Email: {school.email}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            "<font size='15'><b>OFFICIAL SCHOOL FEE RECEIPT</b></font>",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    data = [
        ["Receipt Number", payment.receipt_number],
        ["Date", str(payment.payment_date)],
        ["Student", f"{payment.student.first_name} {payment.student.last_name}"],
        ["Admission No", payment.student.admission_number],
        ["Class", payment.student.school_class.name if payment.student.school_class else ""],
        ["Amount Paid", f"KSh {payment.amount}"],
    ]

    table = Table(data, colWidths=[2.5*inch, 3.5*inch])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))

    elements.append(table)

    elements.append(
        Paragraph("<br/><br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            "Received with thanks.",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph("<br/><br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            "____________________________",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            "Authorized Signature",
            styles["Normal"],
        )
    )

    doc.build(elements)

    return response


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

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

    classes = SchoolClass.objects.all()
    exams = Exam.objects.all()
    subjects = Subject.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        ExamTimetable.objects.create(
            school_class=SchoolClass.objects.get(
                id=request.POST["school_class"]
            ),
            exam=Exam.objects.get(
                id=request.POST["exam"]
            ),
            subject=Subject.objects.get(
                id=request.POST["subject"]
            ),
            exam_date=request.POST["exam_date"],
            day=request.POST["day"],
            start_time=request.POST["start_time"],
            end_time=request.POST["end_time"],
            room=request.POST["room"],
            supervisor=Teacher.objects.get(
                id=request.POST["supervisor"]
            ),
        )

        return redirect("exam_timetable_list")

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
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
    "Teachers",
)
def print_class_exam_timetable(request, id):

    school_class = get_object_or_404(SchoolClass, id=id)

    school = SchoolProfile.objects.first()

    timetables = ExamTimetable.objects.filter(
        school_class=school_class
    ).select_related(
        "exam",
        "subject",
        "supervisor",
    ).order_by(
        "exam_date",
        "start_time",
    )

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
        story.append(
            Paragraph(
                f"<b>{school.name}</b>",
                styles["Title"],
            )
        )

    story.append(
        Paragraph(
            f"<b>{school_class.name} Examination Timetable</b>",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 0.08 * inch))

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

    for t in timetables:

        supervisor = ""

        if t.supervisor:
            supervisor = (
                f"{t.supervisor.first_name} "
                f"{t.supervisor.last_name}"
            )

        data.append([
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
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
    ]))

    story.append(table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"{school_class.name}_Exam_Timetable.pdf",
    )
@login_required
@in_group("Administrators", "Head Teacher")
@login_required
@in_group("Administrators", "Head Teacher")
def edit_exam_timetable(request, id):

    timetable = get_object_or_404(ExamTimetable, id=id)

    classes = SchoolClass.objects.all()
    exams = Exam.objects.all()
    subjects = Subject.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        timetable.school_class = SchoolClass.objects.get(
            id=request.POST["school_class"]
        )

        timetable.exam = Exam.objects.get(
            id=request.POST["exam"]
        )

        timetable.subject = Subject.objects.get(
            id=request.POST["subject"]
        )

        timetable.exam_date = request.POST["exam_date"]
        timetable.day = request.POST["day"]
        timetable.start_time = request.POST["start_time"]
        timetable.end_time = request.POST["end_time"]
        timetable.room = request.POST["room"]

        timetable.supervisor = Teacher.objects.get(
            id=request.POST["supervisor"]
        )

        timetable.save()

        return redirect("exam_timetable_list")

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
    return HttpResponse("Delete Exam Timetable")


from django.http import JsonResponse

@login_required
def load_exams(request):
    class_id = request.GET.get("class_id")

    exams = Exam.objects.filter(
        school_class_id=class_id
    ).values("id", "name")

    return JsonResponse(list(exams), safe=False)

from django.http import JsonResponse

@login_required
def get_class_exams(request, class_id):

    exams = Exam.objects.filter(
        school_class_id=class_id
    )

    data = []

    for exam in exams:
        data.append({
            "id": exam.id,
            "name": exam.name,
            "term": exam.term,
        })

    return JsonResponse(data, safe=False)
@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def inventory_list(request):

    items = InventoryItem.objects.select_related(
        "category"
    ).all().order_by(
        "name"
    )

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "items": items,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def add_inventory_item(request):

    categories = InventoryCategory.objects.all()

    if request.method == "POST":

        InventoryItem.objects.create(

            category=InventoryCategory.objects.get(
                id=request.POST["category"]
            ),

            name=request.POST["name"],

            quantity=request.POST["quantity"],

            unit=request.POST["unit"],

            minimum_stock=request.POST["minimum_stock"],

            location=request.POST["location"],

            description=request.POST["description"],

        )

        messages.success(
            request,
            "Inventory item added successfully."
        )

        return redirect("inventory_list")

    return render(
        request,
        "inventory/add_inventory_item.html",
        {
            "categories": categories,
        },
    )


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def edit_inventory_item(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    categories = InventoryCategory.objects.all()

    if request.method == "POST":

        item.category = InventoryCategory.objects.get(
            id=request.POST["category"]
        )

        item.name = request.POST["name"]
        item.quantity = request.POST["quantity"]
        item.unit = request.POST["unit"]
        item.minimum_stock = request.POST["minimum_stock"]
        item.location = request.POST["location"]
        item.description = request.POST["description"]

        item.save()

        messages.success(
            request,
            "Inventory item updated successfully."
        )

        return redirect("inventory_list")

    return render(
        request,
        "inventory/edit_inventory_item.html",
        {
            "item": item,
            "categories": categories,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def delete_inventory_item(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        item.delete()

        messages.success(
            request,
            "Inventory item deleted successfully."
        )

        return redirect("inventory_list")

    return render(
        request,
        "inventory/delete_inventory_item.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def inventory_category_list(request):

    categories = InventoryCategory.objects.all().order_by("name")

    return render(
        request,
        "inventory/inventory_category_list.html",
        {
            "categories": categories,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def add_inventory_category(request):

    if request.method == "POST":

        InventoryCategory.objects.create(
            name=request.POST["name"]
        )

        messages.success(
            request,
            "Inventory category added successfully."
        )

        return redirect("inventory_category_list")

    return render(
        request,
        "inventory/add_inventory_category.html",
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def receive_stock(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        quantity = int(
            request.POST["quantity"]
        )

        item.quantity += quantity

        item.save()

        StockTransaction.objects.create(

            item=item,

            transaction_type="RECEIVED",

            quantity=quantity,

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Stock received successfully."
        )

        return redirect("inventory_list")

    return render(
        request,
        "inventory/receive_stock.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def issue_stock(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        quantity = int(request.POST["quantity"])

        if quantity > item.quantity:

            messages.error(
                request,
                "Not enough stock available."
            )

            return render(
                request,
                "inventory/issue_stock.html",
                {
                    "item": item,
                },
            )
            

        item.quantity -= quantity
        item.save()

        StockTransaction.objects.create(

            item=item,

            transaction_type="ISSUED",

            quantity=quantity,

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Stock issued successfully."
        )

        return redirect("inventory_list")

    return render(
        request,
        "inventory/issue_stock.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def stock_transaction_list(request):

    transactions = StockTransaction.objects.select_related(
        "item",
        "recorded_by",
    ).order_by("-transaction_date", "-id")

    return render(
        request,
        "inventory/stock_transaction_list.html",
        {
            "transactions": transactions,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Librarian",
    "Head Teacher",
)
def library_list(request):

    books = Book.objects.all().order_by("title")

    return render(
        request,
        "library/library_list.html",
        {
            "books": books,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Librarian",
    "Head Teacher",
)
def add_book(request):

    if request.method == "POST":

        copies = int(request.POST["copies"])

        Book.objects.create(

            title=request.POST["title"],

            author=request.POST["author"],

            isbn=request.POST["isbn"],

            category=request.POST["category"],

            publisher=request.POST["publisher"],

            publication_year=request.POST["publication_year"] or None,

            copies=copies,

            available_copies=copies,

            shelf=request.POST["shelf"],

        )

        messages.success(
            request,
            "Book added successfully."
        )

        return redirect("library_list")

    return render(
        request,
        "library/add_book.html",
    )

@login_required
@in_group("Administrators", "Librarian", "Head Teacher")
def edit_book(request, id):

    book = get_object_or_404(Book, id=id)

    if request.method == "POST":

        book.title = request.POST["title"]
        book.author = request.POST["author"]
        book.isbn = request.POST["isbn"]
        book.category = request.POST["category"]
        book.publisher = request.POST["publisher"]
        book.publication_year = request.POST["publication_year"] or None

        copies = int(request.POST["copies"])

        difference = copies - book.copies

        book.copies = copies
        book.available_copies += difference

        book.shelf = request.POST["shelf"]

        book.save()

        messages.success(request, "Book updated successfully.")

        return redirect("library_list")

    return render(
        request,
        "library/edit_book.html",
        {
            "book": book,
        },
    )


@login_required
@in_group("Administrators", "Librarian")
def delete_book(request, id):

    book = get_object_or_404(Book, id=id)

    if request.method == "POST":

        book.delete()

        messages.success(request, "Book deleted successfully.")

        return redirect("library_list")

    return render(
        request,
        "library/delete_book.html",
        {
            "book": book,
        },
    )

@login_required
@admin_or_teacher
def borrow_book(request):

    students = Student.objects.all().order_by("admission_number")
    books = Book.objects.filter(copies__gt=0).order_by("title")

    if request.method == "POST":

        student = Student.objects.get(id=request.POST["student"])
        book = Book.objects.get(id=request.POST["book"])

        if book.copies <= 0:
            messages.error(request, "This book is out of stock.")
            return redirect("borrow_book")

        BorrowBook.objects.create(
            student=student,
            book=book,
            borrow_date=request.POST["borrow_date"],
            due_date=request.POST["due_date"],
            issued_by=request.user,
        )

        book.copies -= 1
        book.save()

        messages.success(request, "Book borrowed successfully.")

        return redirect("borrow_list")

    return render(
        request,
        "students/borrow_book.html",
        {
            "students": students,
            "books": books,
            "today": date.today(),
        },
    )

@login_required
@admin_or_teacher
def borrow_list(request):

    borrowed_books = BorrowBook.objects.select_related(
        "student",
        "book"
    ).order_by("-borrow_date")

    return render(
        request,
        "students/borrow_list.html",
        {
            "borrowed_books": borrowed_books,
        },
    )

@login_required
@admin_or_teacher
def return_book(request, id):

    borrow = get_object_or_404(BorrowBook, id=id)

    if borrow.status == "Returned":

        messages.warning(
            request,
            "This book has already been returned."
        )

        return redirect("borrow_list")

    borrow.status = "Returned"
    borrow.return_date = date.today()
    borrow.save()

    book = borrow.book
    book.copies += 1
    book.save()

    messages.success(
        request,
        "Book returned successfully."
    )

    return redirect("borrow_list")

from datetime import date
from django.db.models import Sum

@login_required
@admin_or_teacher
def library_dashboard(request):

    total_books = Book.objects.count()

    borrowed_books = BorrowBook.objects.filter(
        status="Borrowed"
    ).count()

    available_books = Book.objects.aggregate(
        total=Sum("available_copies")
    )["total"] or 0

    overdue_books = BorrowBook.objects.filter(
        status="Borrowed",
        due_date__lt=date.today()
    ).count()

    active_borrowers = BorrowBook.objects.filter(
        status="Borrowed"
    ).values("student").distinct().count()

    recent_borrowings = BorrowBook.objects.select_related(
        "student",
        "book"
    ).order_by("-borrow_date")[:10]

    context = {
        "total_books": total_books,
        "borrowed_books": borrowed_books,
        "available_books": available_books,
        "overdue_books": overdue_books,
        "active_borrowers": active_borrowers,
        "recent_borrowings": recent_borrowings,
    }

    return render(
        request,
        "students/library_dashboard.html",
        context,
    )

@login_required
@admin_or_teacher
def library_reports(request):

    borrowed_books = BorrowBook.objects.filter(
        status="Borrowed"
    )

    returned_books = BorrowBook.objects.filter(
        status="Returned"
    )

    overdue_books = BorrowBook.objects.filter(
        status="Borrowed",
        due_date__lt=date.today()
    )

    context = {
        "borrowed_books": borrowed_books,
        "returned_books": returned_books,
        "overdue_books": overdue_books,
    }

    return render(
        request,
        "students/library_reports.html",
        context,
    )

@login_required
@admin_or_teacher
def print_library_report(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
    'inline; filename="library_report.pdf"'
)
    

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>Library Report</b>", styles["Title"])
    )

    elements.append(Spacer(1, 20))

    borrowed = BorrowBook.objects.select_related(
        "student",
        "book"
    ).order_by("-borrow_date")

    data = [
        [
            "Student",
            "Book",
            "Borrow Date",
            "Due Date",
            "Status",
        ]
    ]

    for item in borrowed:

        data.append([
            str(item.student),
            item.book.title,
            str(item.borrow_date),
            str(item.due_date),
            item.status,
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("BACKGROUND",(0,1),(-1,-1),colors.beige),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

    ]))

    elements.append(table)

    doc.build(elements)

    return response

from django.db.models import Avg

@login_required
@admin_or_teacher
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

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg

@login_required
@admin_or_teacher
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

# Transport

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def vehicle_list(request):

    vehicles = Vehicle.objects.select_related(
        "driver"
    ).order_by(
        "registration_number"
    )

    return render(
        request,
        "students/vehicle_list.html",
        {
            "vehicles": vehicles,
        },
    )

@login_required
@admin_or_bursar
def add_vehicle(request):

    drivers = Driver.objects.filter(active=True)

    if request.method == "POST":

        driver = None

        if request.POST.get("driver"):
            driver = Driver.objects.get(id=request.POST["driver"])

        Vehicle.objects.create(
            registration_number=request.POST["registration_number"],
            vehicle_name=request.POST["vehicle_name"],
            make=request.POST["make"],
            capacity=request.POST["capacity"],
            driver=driver,
            status=request.POST["status"],
        )

        return redirect("vehicle_list")

    return render(
        request,
        "students/add_vehicle.html",
        {
            "drivers": drivers,
        },
    )

@login_required
@admin_or_bursar
def edit_vehicle(request, id):

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    drivers = Teacher.objects.all()

    if request.method == "POST":

        vehicle.registration_number = request.POST["registration_number"]
        vehicle.vehicle_name = request.POST["vehicle_name"]
        vehicle.make = request.POST["make"]
        vehicle.capacity = request.POST["capacity"]
        vehicle.status = request.POST["status"]

        if request.POST.get("driver"):
            vehicle.driver = Teacher.objects.get(
                id=request.POST["driver"]
            )
        else:
            vehicle.driver = None

        vehicle.save()

        return redirect("vehicle_list")

    return render(
        request,
        "students/edit_vehicle.html",
        {
            "vehicle": vehicle,
            "drivers": drivers,
        },
    )

@login_required
@admin_or_bursar
def delete_vehicle(request, id):

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    if request.method == "POST":
        vehicle.delete()
        return redirect("vehicle_list")

    return render(
        request,
        "students/delete_vehicle.html",
        {
            "vehicle": vehicle,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def print_vehicle(request, id):

    school = SchoolProfile.objects.first()

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = []

    # School Header

    if school:

        story.append(
            Paragraph(
                f"<font size='18'><b>{school.name}</b></font>",
                styles["Title"],
            )
        )

        story.append(
            Paragraph(
                school.address,
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Tel: {school.phone}",
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Email: {school.email}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 0.25 * inch))

    story.append(
        Paragraph(
            "<b>VEHICLE DETAILS</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    driver = "-"

    if vehicle.driver:
        driver = (
            f"{vehicle.driver.first_name} "
            f"{vehicle.driver.last_name}"
        )

    data = [

        ["Registration Number", vehicle.registration_number],

        ["Vehicle Name", vehicle.vehicle_name],

        ["Make / Model", vehicle.make],

        ["Capacity", str(vehicle.capacity)],

        ["Assigned Driver", driver],

        ["Status", vehicle.status],

    ]

    table = Table(
        data,
        colWidths=[2.6 * inch, 3.8 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),

                ("BACKGROUND", (0, 0), (0, -1), HexColor("#d9edf7")),

                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 0.5 * inch))

    signature_table = Table(
        [
            [
                "_______________________",
                "_______________________",
            ],

            [
                "Transport Officer",
                school.principal_name if school else "Principal",
            ],

            [
                "",
                "Principal",
            ],
        ],
        colWidths=[3 * inch, 3 * inch],
    )

    signature_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(signature_table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=f"{vehicle.registration_number}.pdf",
    )

@login_required
@admin_or_bursar
def transport_route_list(request):

    routes = TransportRoute.objects.select_related(
        "vehicle",
        "driver",
    ).all()

    return render(
        request,
        "students/transport_route_list.html",
        {
            "routes": routes,
        },
    )


@login_required
@admin_or_bursar
def add_transport_route(request):

    vehicles = Vehicle.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        TransportRoute.objects.create(
            route_name=request.POST["route_name"],
            start_point=request.POST["start_point"],
            end_point=request.POST["end_point"],
            distance_km=request.POST["distance_km"],
            vehicle=Vehicle.objects.get(id=request.POST["vehicle"])
            if request.POST["vehicle"] else None,
            driver=Teacher.objects.get(id=request.POST["driver"])
            if request.POST["driver"] else None,
            active="active" in request.POST,
        )

        return redirect("transport_route_list")

    return render(
        request,
        "students/add_transport_route.html",
        {
            "vehicles": vehicles,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def edit_transport_route(request, id):

    route = get_object_or_404(TransportRoute, id=id)

    vehicles = Vehicle.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        route.route_name = request.POST["route_name"]
        route.start_point = request.POST["start_point"]
        route.end_point = request.POST["end_point"]
        route.distance_km = request.POST["distance_km"]

        if request.POST["vehicle"]:
            route.vehicle = Vehicle.objects.get(
                id=request.POST["vehicle"]
            )
        else:
            route.vehicle = None

        if request.POST["driver"]:
            route.driver = Teacher.objects.get(
                id=request.POST["driver"]
            )
        else:
            route.driver = None

        route.active = "active" in request.POST

        route.save()

        return redirect("transport_route_list")

    return render(
        request,
        "students/edit_transport_route.html",
        {
            "route": route,
            "vehicles": vehicles,
            "teachers": teachers,
        },
    )


@login_required
@admin_or_bursar
def delete_transport_route(request, id):

    route = get_object_or_404(
        TransportRoute,
        id=id,
    )

    if request.method == "POST":

        route.delete()

        return redirect("transport_route_list")

    return render(
        request,
        "students/delete_transport_route.html",
        {
            "route": route,
        },
    )

@login_required
@admin_or_bursar
def student_transport_list(request):

    transports = StudentTransport.objects.select_related(
        "student",
        "route",
    ).all()

    return render(
        request,
        "students/student_transport_list.html",
        {
            "transports": transports,
        },
    )

@login_required
@admin_or_bursar
def add_student_transport(request):

    classes = SchoolClass.objects.all().order_by("name")

    class_id = request.GET.get("class")

    students = Student.objects.none()

    if class_id:
        students = Student.objects.filter(
            school_class_id=class_id
        ).order_by("first_name")

    routes = TransportRoute.objects.filter(active=True)

    if request.method == "POST":

        student = Student.objects.get(
            id=request.POST["student"]
        )

        route = TransportRoute.objects.get(
            id=request.POST["route"]
        )

        StudentTransport.objects.create(

            student=student,

            route=route,

            pickup_point=request.POST["pickup_point"],

            dropoff_point=request.POST["dropoff_point"],

            active="active" in request.POST,

        )

        return redirect("student_transport_list")

    return render(
        request,
        "students/add_student_transport.html",
        {
            "classes": classes,
            "students": students,
            "routes": routes,
            "selected_class": class_id,
        },
    )
@login_required
@admin_or_bursar
def edit_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    students = Student.objects.all()

    routes = TransportRoute.objects.filter(
        active=True,
    )

    if request.method == "POST":

        transport.student = Student.objects.get(
            id=request.POST["student"]
        )

        transport.route = TransportRoute.objects.get(
            id=request.POST["route"]
        )

        transport.pickup_point = request.POST["pickup_point"]

        transport.dropoff_point = request.POST["dropoff_point"]

        transport.active = "active" in request.POST

        transport.save()

        return redirect("student_transport_list")

    return render(
        request,
        "students/edit_student_transport.html",
        {
            "transport": transport,
            "students": students,
            "routes": routes,
        },
    )


@login_required
@admin_or_bursar
def delete_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    if request.method == "POST":

        transport.delete()

        return redirect("student_transport_list")

    return render(
        request,
        "students/delete_student_transport.html",
        {
            "transport": transport,
        },
    )

@login_required
@admin_or_bursar
def print_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Transport_{transport.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Student Transport Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Student: {transport.student.first_name} {transport.student.last_name}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Admission No: {transport.student.admission_number}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Route: {transport.route.route_name}"
    )

    y -= 25

    if transport.route.vehicle:

        p.drawString(
            50,
            y,
            f"Vehicle: {transport.route.vehicle.registration_number}"
        )

    else:

        p.drawString(
            50,
            y,
            "Vehicle: None"
        )

    y -= 25

    if transport.route.driver:

        p.drawString(
            50,
            y,
            f"Driver: {transport.route.driver.first_name} {transport.route.driver.last_name}"
        )

    else:

        p.drawString(
            50,
            y,
            "Driver: None"
        )

    y -= 25

    p.drawString(
        50,
        y,
        f"Pickup Point: {transport.pickup_point}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Dropoff Point: {transport.dropoff_point}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Assigned Date: {transport.assigned_date}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if transport.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

from reportlab.pdfgen import canvas

@login_required
@admin_or_bursar
def print_transport_route(request, id):

    route = get_object_or_404(TransportRoute, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Route_{route.route_name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Transport Route Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Route: {route.route_name}")
    y -= 25

    p.drawString(50, y, f"Start Point: {route.start_point}")
    y -= 25

    p.drawString(50, y, f"End Point: {route.end_point}")
    y -= 25

    if route.vehicle:
        p.drawString(
            50,
            y,
            f"Vehicle: {route.vehicle.registration_number}"
        )
    else:
        p.drawString(50, y, "Vehicle: None")

    y -= 25

    if route.driver:
        p.drawString(
            50,
            y,
            f"Driver: {route.driver.first_name} {route.driver.last_name}"
        )
    else:
        p.drawString(50, y, "Driver: None")

    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if route.active else 'Inactive'}"
    )

    p.save()

    return response

from reportlab.pdfgen import canvas


@login_required
@admin_or_bursar
def driver_list(request):

    drivers = Driver.objects.all().order_by("first_name")

    return render(
        request,
        "students/driver_list.html",
        {"drivers": drivers},
    )


@login_required
@admin_or_bursar
def add_driver(request):

    if request.method == "POST":

        Driver.objects.create(
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            phone=request.POST["phone"],
            national_id=request.POST["national_id"],
            license_number=request.POST["license_number"],
            license_expiry=request.POST["license_expiry"],
            active="active" in request.POST,
        )

        return redirect("driver_list")

    return render(request, "students/add_driver.html")


@login_required
@admin_or_bursar
def edit_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    if request.method == "POST":

        driver.first_name = request.POST["first_name"]
        driver.last_name = request.POST["last_name"]
        driver.phone = request.POST["phone"]
        driver.national_id = request.POST["national_id"]
        driver.license_number = request.POST["license_number"]
        driver.license_expiry = request.POST["license_expiry"]
        driver.active = "active" in request.POST

        driver.save()

        return redirect("driver_list")

    return render(
        request,
        "students/edit_driver.html",
        {"driver": driver},
    )


@login_required
@admin_or_bursar
def delete_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    if request.method == "POST":
        driver.delete()
        return redirect("driver_list")

    return render(
        request,
        "students/delete_driver.html",
        {"driver": driver},
    )


@login_required
@admin_or_bursar
def print_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Driver_{driver.id}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "Driver Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Name: {driver.first_name} {driver.last_name}")
    y -= 25

    p.drawString(50, y, f"Phone: {driver.phone}")
    y -= 25

    p.drawString(50, y, f"National ID: {driver.national_id}")
    y -= 25

    p.drawString(50, y, f"License No: {driver.license_number}")
    y -= 25

    p.drawString(50, y, f"License Expiry: {driver.license_expiry}")
    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if driver.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def transport_dashboard(request):

    total_vehicles = Vehicle.objects.count()

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).count()

    total_drivers = Driver.objects.count()

    total_routes = TransportRoute.objects.count()

    total_students = StudentTransport.objects.count()

    recent_assignments = StudentTransport.objects.select_related(
        "student",
        "route",
    ).order_by("-id")[:10]

    context = {

        "total_vehicles": total_vehicles,

        "available_vehicles": available_vehicles,

        "total_drivers": total_drivers,

        "total_routes": total_routes,

        "total_students": total_students,

        "recent_assignments": recent_assignments,

    }

    return render(
        request,
        "students/transport_dashboard.html",
        context,
    )

@login_required
@admin_or_bursar
def hostel_dashboard(request):

    total_blocks = HostelBlock.objects.count()

    total_rooms = HostelRoom.objects.count()

    total_students = StudentHostel.objects.filter(
        active=True
    ).count()

    recent_allocations = StudentHostel.objects.select_related(
        "student",
        "room",
        "room__block"
    ).order_by("-id")[:10]

    context = {

        "total_blocks": total_blocks,

        "total_rooms": total_rooms,

        "total_students": total_students,

        "recent_allocations": recent_allocations,

    }

    return render(
        request,
        "students/hostel_dashboard.html",
        context,
    )

@login_required
@admin_or_bursar
def hostel_block_list(request):

    blocks = HostelBlock.objects.all()

    return render(
        request,
        "students/hostel_block_list.html",
        {"blocks": blocks},
    )


@login_required
@admin_or_bursar
def add_hostel_block(request):

    if request.method == "POST":

        HostelBlock.objects.create(

            name=request.POST["name"],

            description=request.POST["description"],

            active="active" in request.POST,

        )

        return redirect("hostel_block_list")

    return render(
        request,
        "students/add_hostel_block.html")


@login_required
@admin_or_bursar
def edit_hostel_block(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    if request.method == "POST":

        block.name = request.POST["name"]

        block.description = request.POST["description"]

        block.active = "active" in request.POST

        block.save()

        return redirect("hostel_block_list")

    return render(
        request,
        "students/edit_hostel_block.html",
        {"block": block},
    )


@login_required
@admin_or_bursar
def delete_hostel_block(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    if request.method == "POST":

        block.delete()

        return redirect("hostel_block_list")

    return render(
        request,
        "students/delete_hostel_block.html",
        {"block": block},
    )

from reportlab.pdfgen import canvas

@login_required
@admin_or_bursar
def print_hostel_block(request, id):

    block = get_object_or_404(HostelBlock, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Block_{block.name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Block Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Block Name: {block.name}")
    y -= 30

    p.drawString(50, y, f"Description: {block.description}")
    y -= 30

    p.drawString(
        50,
        y,
        f"Status: {'Active' if block.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_room_list(request):

    rooms = HostelRoom.objects.select_related("block")

    return render(
        request,
        "students/hostel_room_list.html",
        {
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_room(request):

    blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        block = HostelBlock.objects.get(
            id=request.POST["block"]
        )

        room = HostelRoom.objects.create(
            block=block,
            room_number=request.POST["room_number"],
            capacity=int(request.POST["capacity"]),
        )

        # Automatically create beds
        for number in range(1, room.capacity + 1):

            HostelBed.objects.create(
                room=room,
                bed_number=f"Bed {number}",
            )

        messages.success(
            request,
            f"Room {room.room_number} created with {room.capacity} beds."
        )

        return redirect("hostel_room_list")

    return render(
        request,
        "students/add_hostel_room.html",
        {
            "blocks": blocks,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_room(request, id):

    room = get_object_or_404(
        HostelRoom,
        id=id,
    )

    blocks = HostelBlock.objects.filter(
        active=True,
    )

    if request.method == "POST":

        room.block = HostelBlock.objects.get(
            id=request.POST["block"]
        )

        room.room_number = request.POST["room_number"]

        new_capacity = int(request.POST["capacity"])

        occupied_beds = HostelBed.objects.filter(
            room=room,
            occupied=True,
        ).count()

        if new_capacity < occupied_beds:

            messages.error(
                request,
                f"Capacity cannot be reduced below {occupied_beds} occupied beds."
            )

            return redirect(
                "edit_hostel_room",
                id=room.id,
            )

        old_capacity = room.capacity

        room.capacity = new_capacity

        room.save()

        # If capacity increased, create new beds
        if new_capacity > old_capacity:

            for number in range(old_capacity + 1, new_capacity + 1):

                HostelBed.objects.create(
                    room=room,
                    bed_number=f"Bed {number}",
                )

        # If capacity reduced, remove only unused highest-numbered beds
        elif new_capacity < old_capacity:

            beds_to_remove = HostelBed.objects.filter(
                room=room,
                occupied=False,
            ).order_by("-id")

            excess = old_capacity - new_capacity

            for bed in beds_to_remove[:excess]:
                bed.delete()

        messages.success(
            request,
            "Hostel room updated successfully."
        )

        return redirect(
            "hostel_room_list"
        )

    return render(
        request,
        "students/edit_hostel_room.html",
        {
            "room": room,
            "blocks": blocks,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_room(request, id):

    room = get_object_or_404(HostelRoom, id=id)

    if request.method == "POST":

        room.delete()

        return redirect("hostel_room_list")

    return render(
        request,
        "students/delete_hostel_room.html",
        {"room": room},
    )

@login_required
@admin_or_bursar
def print_hostel_room(request, id):

    room = get_object_or_404(HostelRoom, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Room_{room.room_number}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Room Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Block: {room.block.name}")
    y -= 30

    p.drawString(50, y, f"Room: {room.room_number}")
    y -= 30

    p.drawString(50, y, f"Capacity: {room.capacity}")
    y -= 30

    p.drawString(50, y, f"Occupied: {room.occupied}")

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def student_hostel_list(request):

    allocations = StudentHostel.objects.select_related(
        "student",
        "room",
        "room__block"
    )

    return render(
        request,
        "students/student_hostel_list.html",
        {"allocations": allocations},
    )

@login_required
@admin_or_bursar
def add_student_hostel(request):

    students = Student.objects.filter(
        hostel__isnull=True
    )

    rooms = HostelRoom.objects.select_related(
        "block"
    )

    if request.method == "POST":

        student = Student.objects.get(
            id=request.POST["student"]
        )

        room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        bed = HostelBed.objects.get(
            id=request.POST["bed"]
        )

        if bed.occupied:

            messages.error(
                request,
                "This bed is already occupied."
            )

            return redirect(
                "add_student_hostel"
            )

        StudentHostel.objects.create(

            student=student,

            room=room,

            bed=bed,

        )

        bed.occupied = True
        bed.save()

        messages.success(
            request,
            "Student allocated successfully."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/add_student_hostel.html",
        {
            "students": students,
            "rooms": rooms,
        },
    )
@login_required
@admin_or_bursar
def edit_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
    )

    rooms = HostelRoom.objects.select_related(
        "block"
    )

    if request.method == "POST":

        new_room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        new_bed = HostelBed.objects.get(
            id=request.POST["bed"]
        )

        if new_bed.occupied and new_bed != allocation.bed:

            messages.error(
                request,
                "Selected bed is already occupied."
            )

            return redirect(
                "edit_student_hostel",
                id=id,
            )

        # Free old bed
        allocation.bed.occupied = False
        allocation.bed.save()

        # Occupy new bed
        new_bed.occupied = True
        new_bed.save()

        allocation.room = new_room
        allocation.bed = new_bed

        allocation.save()

        messages.success(
            request,
            "Allocation updated successfully."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/edit_student_hostel.html",
        {
            "allocation": allocation,
            "rooms": rooms,
        },
    )
@login_required
@admin_or_bursar
def delete_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
    )

    if request.method == "POST":

        allocation.bed.occupied = False
        allocation.bed.save()

        allocation.delete()

        messages.success(
            request,
            "Student removed from hostel."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/delete_student_hostel.html",
        {
            "allocation": allocation,
        },
    )
@login_required
@admin_or_bursar
def print_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel.objects.select_related(
            "student",
            "room",
            "room__block",
            "bed",
        ),
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Allocation_{allocation.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL ALLOCATION",
    )

    y = 690

    p.drawString(
        50,
        y,
        f"Admission Number : {allocation.student.admission_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Student : {allocation.student.first_name} {allocation.student.last_name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Class : {allocation.student.school_class}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Hostel Block : {allocation.room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room : {allocation.room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Bed : {allocation.bed.bed_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Assigned : {allocation.assigned_date}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_warden_list(request):

    wardens = HostelWarden.objects.select_related(
        "hostel_block"
    )

    return render(
        request,
        "students/hostel_warden_list.html",
        {
            "wardens": wardens,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_warden(request):

    hostel_blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        HostelWarden.objects.create(

            first_name=request.POST["first_name"],

            last_name=request.POST["last_name"],

            gender=request.POST["gender"],

            phone=request.POST["phone"],

            email=request.POST["email"],

            hostel_block=HostelBlock.objects.get(
                id=request.POST["hostel_block"]
            ),

            active="active" in request.POST,

        )

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/add_hostel_warden.html",
        {
            "hostel_blocks": hostel_blocks,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    hostel_blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        warden.first_name = request.POST["first_name"]
        warden.last_name = request.POST["last_name"]
        warden.gender = request.POST["gender"]
        warden.phone = request.POST["phone"]
        warden.email = request.POST["email"]

        warden.hostel_block = HostelBlock.objects.get(
            id=request.POST["hostel_block"]
        )

        warden.active = "active" in request.POST

        warden.save()

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/edit_hostel_warden.html",
        {
            "warden": warden,
            "hostel_blocks": hostel_blocks,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    if request.method == "POST":

        warden.delete()

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/delete_hostel_warden.html",
        {
            "warden": warden,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Warden_{warden.first_name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(170, 800, "Hostel Warden Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Name: {warden.first_name} {warden.last_name}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Gender: {warden.gender}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Phone: {warden.phone}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Email: {warden.email}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Hostel Block: {warden.hostel_block}",
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_transfer_list(request):

    transfers = HostelTransfer.objects.select_related(
        "student",
        "from_room",
        "to_room",
    ).order_by("-transfer_date")

    return render(
        request,
        "students/hostel_transfer_list.html",
        {
            "transfers": transfers,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_transfer(request):

    allocations = StudentHostel.objects.select_related(
        "student",
        "room",
    )

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        allocation = StudentHostel.objects.get(
            id=request.POST["allocation"]
        )

        new_room = HostelRoom.objects.get(
            id=request.POST["to_room"]
        )

        # Prevent transferring to the same room
        if allocation.room == new_room:

            messages.error(
                request,
                "Student is already in this room."
            )

            return redirect("add_hostel_transfer")

        # Check room capacity
        if new_room.is_full:

            messages.error(
                request,
                "The selected room is already full."
            )

            return redirect("add_hostel_transfer")

        HostelTransfer.objects.create(

            student=allocation.student,

            from_room=allocation.room,

            to_room=new_room,

            reason=request.POST["reason"],

            transferred_by=request.user,

        )

        allocation.room = new_room

        allocation.save()

        messages.success(
            request,
            "Student transferred successfully."
        )

        return redirect("hostel_transfer_list")

    return render(
        request,
        "students/add_hostel_transfer.html",
        {
            "allocations": allocations,
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_transfer(request, id):

    transfer = get_object_or_404(
        HostelTransfer,
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Transfer_{transfer.student}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Transfer")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Student: {transfer.student}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"From Room: {transfer.from_room}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"To Room: {transfer.to_room}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Transfer Date: {transfer.transfer_date}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Reason: {transfer.reason}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Transferred By: {transfer.transferred_by}",
    )

    p.showPage()

    p.save()

    return response

@login_required
@admin_or_bursar
def print_hostel_room(request, id):

    room = get_object_or_404(
        HostelRoom.objects.select_related("block"),
        id=id,
    )

    allocations = room.students.select_related(
        "student",
        "student__school_class",
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Room_{room.room_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL ROOM REPORT",
    )

    y = 690
    p.drawString(
        50,
        y,
        f"Hostel Block : {room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room Number : {room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Capacity : {room.capacity}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Occupied Beds : {room.occupied_beds}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Available Beds : {room.available_beds}",
    )

    y -= 20

    occupancy = 0

    if room.capacity > 0:
        occupancy = round(
            (room.occupied_beds / room.capacity) * 100,
            1,
        )

    p.drawString(
        50,
        y,
        f"Occupancy Rate : {occupancy}%",
    )

    y -= 40

    # ---------------------------------------
    # STUDENTS
    # ---------------------------------------

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        50,
        y,
        "Students in this Room",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y, "No")
    p.drawString(80, y, "Admission")
    p.drawString(160, y, "Student Name")
    p.drawString(340, y, "Class")
    p.drawString(450, y, "Bed")

    y -= 10

    p.line(50, y, 550, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for index, allocation in enumerate(allocations, start=1):

        student = allocation.student

        p.drawString(
            50,
            y,
            str(index),
        )

        p.drawString(
            80,
            y,
            student.admission_number,
        )

        p.drawString(
            160,
            y,
            f"{student.first_name} {student.last_name}",
        )

        p.drawString(
            340,
            y,
            str(student.school_class),
        )

        p.drawString(
            450,
            y,
            str(allocation.bed_number),
        )

        y -= 18

        # Start a new page if needed
        if y < 60:

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL ROOM REPORT",
            )

            y = 690

            p.setFont("Helvetica-Bold", 10)

            p.drawString(50, y, "No")
            p.drawString(80, y, "Admission")
            p.drawString(160, y, "Student Name")
            p.drawString(340, y, "Class")
            p.drawString(450, y, "Bed")

            y -= 10

            p.line(50, y, 550, y)

            y -= 18

            p.setFont("Helvetica", 10)

   # ---------------------------------------
    # FOOTER
    # ---------------------------------------

    draw_school_footer(
        p,
        request,
    )

    p.setFont("Helvetica-Bold", 10)

    p.drawRightString(
        550,
        55,
        f"Total Students: {room.occupied_beds}",
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_occupancy_report(request):

    blocks = HostelBlock.objects.filter(active=True)

    selected_block = None
    rooms = []

    total_rooms = 0
    total_capacity = 0
    total_occupied = 0
    total_available = 0
    occupancy_rate = 0

    if "block" in request.GET:

        selected_block = get_object_or_404(
            HostelBlock,
            id=request.GET["block"],
        )

        rooms = HostelRoom.objects.filter(
            block=selected_block
        )

        total_rooms = rooms.count()

        for room in rooms:

            total_capacity += room.capacity
            total_occupied += room.occupied_beds
            total_available += room.available_beds

        if total_capacity > 0:

            occupancy_rate = round(
                (total_occupied / total_capacity) * 100,
                1,
            )

    return render(
        request,
        "students/hostel_occupancy_report.html",
        {
            "blocks": blocks,
            "selected_block": selected_block,
            "rooms": rooms,
            "total_rooms": total_rooms,
            "total_capacity": total_capacity,
            "total_occupied": total_occupied,
            "total_available": total_available,
            "occupancy_rate": occupancy_rate,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_occupancy_report(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    rooms = HostelRoom.objects.filter(
        block=block
    ).order_by("room_number")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Occupancy_{block.name}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL OCCUPANCY REPORT",
    )

    y = 690

    total_rooms = rooms.count()
    total_capacity = 0
    total_occupied = 0
    total_available = 0

    for room in rooms:

        total_capacity += room.capacity
        total_occupied += room.occupied_beds
        total_available += room.available_beds

    occupancy_rate = 0

    if total_capacity > 0:

        occupancy_rate = round(
            (total_occupied / total_capacity) * 100,
            1,
        )

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        f"Hostel Block : {block.name}",
    )

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        50,
        y,
        f"Total Rooms : {total_rooms}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Total Capacity : {total_capacity}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Occupied Beds : {total_occupied}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Available Beds : {total_available}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Occupancy Rate : {occupancy_rate}%",
    )

    y -= 35

    # Table Header

    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y, "Room")

    p.drawString(150, y, "Capacity")

    p.drawString(250, y, "Occupied")

    p.drawString(350, y, "Available")

    p.drawString(460, y, "Status")

    y -= 10

    p.line(50, y, 550, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for room in rooms:

        if room.is_full:
            status = "FULL"
        elif room.occupied_beds == 0:
            status = "EMPTY"
        else:
            status = "AVAILABLE"

        p.drawString(
            50,
            y,
            room.room_number,
        )

        p.drawString(
            150,
            y,
            str(room.capacity),
        )

        p.drawString(
            250,
            y,
            str(room.occupied_beds),
        )

        p.drawString(
            350,
            y,
            str(room.available_beds),
        )

        p.drawString(
            460,
            y,
            status,
        )

        y -= 18

        if y < 70:

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL OCCUPANCY REPORT",
            )

            y = 690

            p.setFont("Helvetica-Bold", 10)

            p.drawString(50, y, "Room")
            p.drawString(150, y, "Capacity")
            p.drawString(250, y, "Occupied")
            p.drawString(350, y, "Available")
            p.drawString(460, y, "Status")

            y -= 10

            p.line(50, y, 550, y)

            y -= 18

            p.setFont("Helvetica", 10)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_bed_list(request):

    beds = HostelBed.objects.select_related(
        "room",
        "room__block",
    ).order_by(
        "room__block__name",
        "room__room_number",
        "bed_number",
    )

    return render(
        request,
        "students/hostel_bed_list.html",
        {
            "beds": beds,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_bed(request):

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        HostelBed.objects.create(

            room=room,

            bed_number=request.POST["bed_number"],

        )

        messages.success(
            request,
            "Bed added successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/add_hostel_bed.html",
        {
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed,
        id=id,
    )

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        bed.room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        bed.bed_number = request.POST["bed_number"]

        bed.save()

        messages.success(
            request,
            "Bed updated successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/edit_hostel_bed.html",
        {
            "bed": bed,
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed,
        id=id,
    )

    if request.method == "POST":

        bed.delete()

        messages.success(
            request,
            "Bed deleted successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/delete_hostel_bed.html",
        {
            "bed": bed,
        },
    )

@login_required
@admin_or_bursar
def generate_hostel_beds(request, id):

    room = get_object_or_404(
        HostelRoom,
        id=id,
    )

    created = 0

    for number in range(1, room.capacity + 1):

        bed_number = f"Bed {number}"

        bed, was_created = HostelBed.objects.get_or_create(
            room=room,
            bed_number=bed_number,
        )

        if was_created:
            created += 1

    messages.success(
        request,
        f"{created} bed(s) generated successfully."
    )

    return redirect("hostel_room_list")

@login_required
@admin_or_bursar
def print_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed.objects.select_related(
            "room",
            "room__block",
        ),
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Bed_{bed.bed_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL BED REPORT",
    )

    y = 690

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Hostel Block : {bed.room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room : {bed.room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Bed : {bed.bed_number}",
    )

    y -= 20

    status = "Occupied" if bed.occupied else "Available"

    p.drawString(
        50,
        y,
        f"Status : {status}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

from django.http import JsonResponse

@login_required
@admin_or_bursar
def available_beds(request, room_id):

    beds = HostelBed.objects.filter(
        room_id=room_id,
        occupied=False,
    )

    data = []

    for bed in beds:

        data.append({

            "id": bed.id,

            "name": bed.bed_number,

        })

    return JsonResponse(
        data,
        safe=False,
    )