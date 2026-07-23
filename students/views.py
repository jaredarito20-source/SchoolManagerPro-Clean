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

    context = {
        "school": school,
        "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(),
        "total_classes": SchoolClass.objects.count(),
        "total_subjects": Subject.objects.count(),
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
    student = get_object_or_404(Student, id=id)

    marks = Mark.objects.filter(student=student)

    total = marks.aggregate(Sum("marks"))["marks__sum"] or 0
    average = marks.aggregate(Avg("marks"))["marks__avg"] or 0
    overall_grade = calculate_overall_grade(average)

    # Get all students in the same class
    classmates = Student.objects.filter(
        school_class=student.school_class
    )

    ranking = []

    for s in classmates:
        student_total = (
            Mark.objects.filter(student=s)
            .aggregate(Sum("marks"))["marks__sum"] or 0
        )

        ranking.append({
            "student": s,
            "total": student_total
        })

    # Sort by total marks (highest first)
    ranking.sort(key=lambda x: x["total"], reverse=True)

    position = 1

    for item in ranking:
        if item["student"].id == student.id:
            break
        position += 1

    context = {
        "student": student,
        "marks": marks,
        "total": total,
        "average": round(average, 2),
        "overall_grade": overall_grade,
        "position": position,
        "class_size": classmates.count(),
    }
    return render(request, "students/student_report.html", context)



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
@admin_or_teacher
def print_report(request, id):
    student = get_object_or_404(Student, id=id)
    marks = Mark.objects.filter(student=student)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{student.admission_number}_report.pdf"'
    )

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("<b>STUDENT REPORT CARD</b>", styles["Title"]))
    elements.append(Paragraph(f"Student: {student.first_name} {student.last_name}", styles["Normal"]))
    elements.append(Paragraph(f"Admission No: {student.admission_number}", styles["Normal"]))

    if student.school_class:
        elements.append(Paragraph(f"Class: {student.school_class.name}", styles["Normal"]))

    elements.append(Paragraph("<br/>", styles["Normal"]))

    data = [["Subject", "Marks", "Grade"]]

    total = 0

    for mark in marks:
        data.append([
            mark.subject.name,
            str(mark.marks),
            mark.grade,
        ])
        total += mark.marks

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))

    elements.append(table)

    average = total / marks.count() if marks.count() else 0

    elements.append(Paragraph("<br/>", styles["Normal"]))
    elements.append(Paragraph(f"<b>Total Marks:</b> {total}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Average:</b> {average:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Overall Grade:</b> {calculate_overall_grade(average)}", styles["Normal"]))

    doc.build(elements)

    return response
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
@in_group("Bursar")
def add_payment(request):

    if request.method == "POST":

        student = Student.objects.get(
            id=request.POST["student"]
        )

        FeePayment.objects.create(
            student=student,
            amount_paid=request.POST["amount_paid"],
            receipt_number=request.POST["receipt_number"],
        )

        return redirect("payment_list")

    students = Student.objects.all()

    return render(
        request,
        "students/add_payment.html",
        {"students": students},
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
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all()

    return render(
        request,
        "students/user_list.html",
        {
            "users": users,
        },
    )