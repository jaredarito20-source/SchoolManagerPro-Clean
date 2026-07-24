from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Sum, Avg
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.http import HttpResponse
from datetime import date
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, get_object_or_404

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
from reportlab.lib.units import inch
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
)
from .decorators import (
    admin_required,
    teacher_required,
    bursar_required,
    secretary_required,
    admin_or_teacher,
    admin_or_bursar,
    admin_teacher_secretary,
)
# ======================================
# User Role Checks
# ======================================

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




def in_group(group_name):
    def check(user):
        return (
            user.is_superuser or
            (
                user.is_authenticated and
                user.groups.filter(name=group_name).exists()
            )
        )
    return user_passes_test(check)


@login_required
@admin_required
def home(request):
    school = SchoolProfile.objects.first()

    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = SchoolClass.objects.count()
    total_subjects = Subject.objects.count()

    total_payments = FeePayment.objects.aggregate(
        total=Sum("amount_paid")
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
@admin_required
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
@admin_required
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
@admin_teacher_secretary
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == "POST":
        student.delete()
        return redirect("student_list")

    return render(request, "students/delete_student.html", {
        "student": student
    })


@login_required
@admin_required
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, "students/teacher_list.html", {
        "teachers": teachers
    })


@login_required
@admin_required
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
@admin_required
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
@admin_required
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)

    if request.method == "POST":
        teacher.delete()
        return redirect("teacher_list")

    return render(request, "students/delete_teacher.html", {
        "teacher": teacher
    })


@login_required
@admin_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "students/subject_list.html", {
        "subjects": subjects
    })



@login_required
@admin_required
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
@admin_required
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
@admin_required
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
    if request.method == "POST":
        student = Student.objects.get(id=request.POST["student"])
        subject = Subject.objects.get(id=request.POST["subject"])
        exam = Exam.objects.get(id=request.POST["exam"])

        marks = float(request.POST["marks"])

        # Check for duplicate
        if Mark.objects.filter(
            student=student,
            subject=subject,
            exam=exam
        ).exists():

            students = Student.objects.all()
            subjects = Subject.objects.all()
            exams = Exam.objects.all()

            return render(request, "students/add_mark.html", {
                "students": students,
                "subjects": subjects,
                "exams": exams,
                "error": "Marks for this student, subject and exam already exist."
            })

        Mark.objects.create(
            student=student,
            subject=subject,
            exam=exam,
            marks=marks,
            grade=calculate_grade(marks),
        )

        return redirect("mark_list")

    students = Student.objects.all()
    subjects = Subject.objects.all()
    exams = Exam.objects.all()

    return render(request, "students/add_mark.html", {
        "students": students,
        "subjects": subjects,
        "exams": exams,
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
            )

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

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    story = []
    if school and school.logo:
        try:
            logo = Image(
                school.logo.path,
                width=70,
                height=70,
            )
            story.append(logo)
        except Exception:
            pass
    story.append(
        Paragraph(
            f"<b>{school.name}</b>",
            title,
        )
    )
   
    if school.motto:
        story.append(
            Paragraph(
                school.motto,
                styles["Italic"],
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
            f"Phone: {school.phone}",
            styles["Normal"],
        )
    )

    if school.email:
        story.append(
            Paragraph(
                school.email,
                styles["Normal"],
            )
        )

    story.append(
        Paragraph(
            f"{school.current_term} | {school.academic_year}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "<b>STUDENT REPORT CARD</b>",
            title,
        )
    )

    story.append(Spacer(1, 0.3 * inch))
    

    

    
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

                ("BACKGROUND", (0, 0), (0, -1), HexColor("#d9edf7")),

                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

            ]

        )

    )

    story.append(info_table)

    if student.photo:
        try:
            photo = Image(
                student.photo.path,
                width=90,
                height=110,
            )
            story.append(photo)
        except Exception:
            pass
    story.append(Spacer(1, 0.3 * inch))

    data = [

        ["No", "Subject", "Marks", "Grade"]

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

    results = Table(
        data,
        colWidths=[0.6 * inch, 3.5 * inch, 1 * inch, 1 * inch],
    )

    results.setStyle(

        TableStyle(

            [

                ("GRID", (0, 0), (-1, -1), 1, colors.black),

                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4472C4")),

                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("ALIGN", (0, 0), (-1, -1), "CENTER"),

                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

            ]

        )

    )

    story.append(results)

    story.append(Spacer(1, 0.3 * inch))

    # Performance Summary
    summary = [
        ["Total Marks", total],
        ["Average", average],
        ["Overall Grade", overall_grade],
    ]

    summary_table = Table(
        summary,
        colWidths=[2.5 * inch, 2 * inch],
    )

    summary_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#d9edf7")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(summary_table)

    story.append(Spacer(1, 0.3 * inch))

    # Fee Summary
    total_fee = student.total_fee()
    total_paid = student.total_paid()
    balance = student.balance()

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

    story.append(Spacer(1, 0.4 * inch))

    # Teacher's Remark
    if average >= 80:
        remark = "Excellent Performance. Keep it up."
    elif average >= 70:
        remark = "Very Good Performance."
    elif average >= 60:
        remark = "Good Work. Keep Improving."
    elif average >= 50:
        remark = "Fair Performance."
    else:
        remark = "Needs More Effort."

    story.append(
        Paragraph(
            "<b>Teacher's Remarks</b>",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            remark,
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.5 * inch))

    # Signature Section
    # Signature Section

    story.append(
        Spacer(1, 0.5 * inch)
    )


    signature_content = []


# Principal Signature Image
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
                "________________________",
                signature_content[0],
            ],

            [
                "Class Teacher",
                school.principal_name or "Principal",
            ],

            [
                "",
                "Principal",
            ],
        ],

        colWidths=[
            3 * inch,
            3 * inch,
        ],
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

    story.append(Spacer(1, 0.3 * inch))

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
def print_receipt(request, id):

    payment = get_object_or_404(
        FeePayment,
        id=id
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Receipt_{payment.receipt_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b>SCHOOL MANAGEMENT SYSTEM</b>",
            styles["Title"],
        )
    )

    elements.append(
        Paragraph(
            "<b>OFFICIAL FEE RECEIPT</b>",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            f"<b>Receipt Number:</b> {payment.receipt_number}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Student:</b> {payment.student.first_name} {payment.student.last_name}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Admission No:</b> {payment.student.admission_number}",
            styles["Normal"],
        )
    )

    if payment.student.school_class:
        elements.append(
            Paragraph(
                f"<b>Class:</b> {payment.student.school_class.name}",
                styles["Normal"],
            )
        )

    elements.append(
        Paragraph(
            f"<b>Amount Paid:</b> KSh {payment.amount_paid}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date:</b> {payment.date_paid}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            "<b>Thank you for your payment.</b>",
            styles["Heading2"],
        )
    )

    doc.build(elements)

    return response



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
@in_group("Bursar")
def payment_list(request):

    payments = FeePayment.objects.all()

    return render(
        request,
        "students/payment_list.html",
        {"payments": payments},
    )

@login_required
@admin_or_bursar
def add_payment(request):

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"]
        )

        last_payment = FeePayment.objects.order_by("-id").first()

        if last_payment:
            last_number = int(last_payment.receipt_number.replace("RCP", ""))
            receipt_number = f"RCP{last_number + 1:06d}"
        else:
            receipt_number = "RCP000001"

        FeePayment.objects.create(
            student=student,
            amount_paid=request.POST["amount_paid"],
            receipt_number=receipt_number,
        )

        messages.success(
            request,
            f"Payment recorded successfully. Receipt No. {receipt_number}"
        )

        return redirect("payment_list")

    students = Student.objects.all().order_by(
        "admission_number"
    )

    return render(
        request,
        "students/add_payment.html",
        {
            "students": students,
        },
    )

@login_required
@admin_or_bursar
def print_fee_statement(request, id):

    student = get_object_or_404(Student, id=id)

    school = SchoolProfile.objects.first()

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("payment_date")

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="Fee_Statement_{student.admission_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    if school:
        elements.append(
            Paragraph(
                f"<b><font size='18'>{school.name}</font></b>",
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
            "<b>STUDENT FEE STATEMENT</b>",
            styles["Heading1"],
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            f"<b>Student:</b> {student.first_name} {student.last_name}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Admission No:</b> {student.admission_number}",
            styles["Normal"],
        )
    )

    if student.school_class:
        elements.append(
            Paragraph(
                f"<b>Class:</b> {student.school_class.name}",
                styles["Normal"],
            )
        )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    data = [["Receipt", "Date", "Amount"]]

    for payment in payments:
        data.append([
            payment.receipt_number,
            str(payment.payment_date),
            f"KSh {payment.amount_paid}",
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
    ]))

    elements.append(table)

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph(
            f"<b>Total Fee:</b> KSh {student.total_fee()}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Total Paid:</b> KSh {student.total_paid()}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Balance:</b> KSh {student.balance()}",
            styles["Heading2"],
        )
    )

    doc.build(elements)

    return response

@login_required
@admin_or_bursar
def fee_statement(request, id):

    student = get_object_or_404(Student, id=id)

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("-payment_date")

    context = {
        "student": student,
        "payments": payments,
        "total_fee": student.total_fee(),
        "total_paid": student.total_paid(),
        "balance": student.balance(),
    }

    return render(
        request,
        "students/fee_statement.html",
        context,
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
@admin_teacher_secretary
def attendance_list(request):
    attendance = Attendance.objects.all().order_by("-date")

    return render(
        request,
        "students/attendance_list.html",
        {
            "attendance": attendance,
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


@login_required
@admin_teacher_secretary
def take_attendance(request):

    classes = SchoolClass.objects.all()

    selected_class = None
    students = []

    if request.method == "POST":

        school_class = SchoolClass.objects.get(
            id=request.POST["school_class"]
        )

        attendance_date = request.POST["date"]

        students = Student.objects.filter(
            school_class=school_class
        )

        for student in students:

            status = request.POST.get(
                f"status_{student.id}",
                "Present"
            )

            Attendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    "school_class": school_class,
                    "status": status,
                }
            )

        return redirect("attendance_list")

    class_id = request.GET.get("class")

    if class_id:
        selected_class = SchoolClass.objects.get(id=class_id)

        students = Student.objects.filter(
            school_class=selected_class
        )

    return render(
        request,
        "students/take_attendance.html",
        {
            "classes": classes,
            "selected_class": selected_class,
            "students": students,
            "today": date.today(),
        },
    )


@login_required
@admin_teacher_secretary
def edit_attendance(request, id):
    attendance = get_object_or_404(
        Attendance,
        id=id
    )

    if request.method == "POST":
        attendance.status = request.POST["status"]
        attendance.save()
        return redirect("attendance_list")

    return render(
        request,
        "students/edit_attendance.html",
        {
            "attendance": attendance
        },
    )


@login_required
@admin_teacher_secretary
def delete_attendance(request, id):
    attendance = get_object_or_404(
        Attendance,
        id=id
    )

    if request.method == "POST":
        attendance.delete()
        return redirect("attendance_list")

    return render(
        request,
        "students/delete_attendance.html",
        {
            "attendance": attendance
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
@admin_or_teacher
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
        ["Amount Paid", f"KSh {payment.amount_paid}"],
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