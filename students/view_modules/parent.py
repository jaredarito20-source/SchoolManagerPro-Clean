from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from students.models import(Student, 
                            FeePayment, 
                            Mark, 
                            Attendance,
                            FeeStructure,
                            Homework, 
                            Subject, 
                            SchoolClass, 
                            Teacher,
                           
)

from django.utils import timezone

from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from ..models import Homework, Subject, SchoolClass, Teacher




@login_required
def parent_dashboard(request):

    children = Student.objects.filter(
        parent_user=request.user
    )

    if request.method == "GET":

        child_id = request.GET.get("child")

        if child_id:

            request.session["selected_child"] = child_id

    selected_child = None

    if "selected_child" in request.session:

        selected_child = children.filter(
            id=request.session["selected_child"]
        ).first()

    if selected_child is None and children.exists():

        selected_child = children.first()

        request.session["selected_child"] = selected_child.id

    return render(
        request,
        "parents/dashboard.html",
        {
            "children": children,
            "selected_child": selected_child,
        },
    )
@login_required
def parent_students(request):

    children = Student.objects.filter(
        parent_user=request.user
    ).order_by("school_class", "first_name")

    return render(
        request,
        "parents/parent_students.html",
        {
            "children": children,
        },
    )



@login_required
def parent_student_profile(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user
    )

    marks = Mark.objects.filter(student=student)

    fee_payments = FeePayment.objects.filter(student=student)

    context = {
        "student": student,
        "marks": marks,
        "fee_payments": fee_payments,
    }

    return render(
        request,
        "parents/student_profile.html",
        context,
    )


def parent_attendance(request):

    children = Student.objects.filter(parent_user=request.user)

    attendance = Attendance.objects.filter(
        student__in=children
    ).order_by("-date")

    return render(
        request,
        "parents/attendance.html",
        {
            "attendance": attendance,
        },
    )






@login_required
def parent_results(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
    )

    marks = (
        Mark.objects
        .filter(student=student)
        .select_related("subject", "exam")
        .order_by("exam__name", "subject__name")
    )

    total = sum(mark.marks for mark in marks)
    count = marks.count()
    average = round(total / count, 2) if count else 0

    context = {
        "student": student,
        "marks": marks,
        "total": total,
        "average": average,
    }

    return render(
        request,
        "parents/results.html",
        context,
    )



@login_required
def parent_fee_statement(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
    )

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("-payment_date")

    total_paid = sum(payment.amount_paid for payment in payments)

    total_fee = fee_structure.total_fee if fee_structure else 0

    balance = total_fee - total_paid

    context = {
        "student": student,
        "fee_structure": fee_structure,
        "payments": payments,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "balance": balance,
    }

    return render(
        request,
        "parents/fee_statement.html",
        context,
    )

from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph


@login_required
def print_fee_statement(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
    )

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    payments = FeePayment.objects.filter(student=student)

    total_paid = sum(payment.amount_paid for payment in payments)

    total_fee = fee_structure.total_fee if fee_structure else 0

    balance = total_fee - total_paid

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Fee_Statement_{student.admission_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>FEE STATEMENT</b>", styles["Title"]))
    story.append(Paragraph(f"Student: {student.first_name} {student.last_name}", styles["Normal"]))
    story.append(Paragraph(f"Admission No: {student.admission_number}", styles["Normal"]))
    story.append(Paragraph(f"Class: {student.school_class}", styles["Normal"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    story.append(Paragraph(f"Total Fees: Ksh {total_fee}", styles["Normal"]))
    story.append(Paragraph(f"Total Paid: Ksh {total_paid}", styles["Normal"]))
    story.append(Paragraph(f"Balance: Ksh {balance}", styles["Normal"]))

    doc.build(story)

    return response

@login_required
def parent_fee_balance(request):

    children = Student.objects.filter(parent_user=request.user)

    fee_data = []

    for child in children:

        fee_structure = FeeStructure.objects.filter(
            school_class=child.school_class
        ).first()

        total_fee = fee_structure.total_fee if fee_structure else 0

        payments = FeePayment.objects.filter(student=child)

        total_paid = sum(payment.amount_paid for payment in payments)

        balance = total_fee - total_paid

        fee_data.append({
            "student": child,
            "total_fee": total_fee,
            "total_paid": total_paid,
            "balance": balance,
        })

    return render(
        request,
        "parents/fee_balance.html",
        {
            "fee_data": fee_data,
        },
    )




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def parent_attendance(request):

    children = Student.objects.filter(parent_user=request.user)

    if not children.exists():
        return render(
            request,
            "parents/attendance.html",
            {
                "student": None,
                "attendance": [],
            },
        )

    child_id = request.session.get("selected_child")

    student = children.filter(id=child_id).first()

    if student is None:
        student = children.first()
        request.session["selected_child"] = student.id

    attendance = Attendance.objects.filter(
        student=student
    ).order_by("-date")

    return render(
        request,
        "parents/attendance.html",
        {
            "student": student,
            "attendance": attendance,
        },
    )
@login_required
def homework_list(request):

    user = request.user

    # Administrator
    if user.is_superuser or user.groups.filter(name="Administrators").exists():

        homework = Homework.objects.select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by("-date_given")

    # Teacher
    elif user.groups.filter(name="Teachers").exists():

        teacher = Teacher.objects.filter(
            user=user
        ).first()

        homework = Homework.objects.filter(
            teacher=teacher
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by("-date_given")

    # Parent
    elif user.groups.filter(name="Parents").exists():

        children = Student.objects.filter(
            parent_user=user
        )

        classes = children.values_list(
            "school_class",
            flat=True,
        )

        homework = Homework.objects.filter(
            school_class__in=classes
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by("-date_given")

    # Student
    else:

        student = Student.objects.filter(
            user=user
        ).first()

        if student:

            homework = Homework.objects.filter(
                school_class=student.school_class
            ).select_related(
                "subject",
                "school_class",
                "teacher",
            ).order_by("-date_given")

        else:

            homework = Homework.objects.none()

    return render(
        request,
        "homework/homework_list.html",
        {
            "homework": homework,
        },
    )
@login_required
def add_homework(request):

    subjects = Subject.objects.all()
    classes = SchoolClass.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        Homework.objects.create(

            subject_id=request.POST["subject"],

            school_class_id=request.POST["school_class"],

            teacher_id=request.POST["teacher"],

            title=request.POST["title"],

            description=request.POST["description"],

            due_date=request.POST["due_date"],

            attachment=request.FILES.get("attachment"),

        )

        messages.success(
            request,
            "Homework added successfully."
        )

        return redirect("homework_list")

    return render(
        request,
        "homework/add_homework.html",
        {
            "subjects": subjects,
            "classes": classes,
            "teachers": teachers,
        },
    )

@login_required
def edit_homework(request, pk):

    homework = get_object_or_404(
        Homework,
        pk=pk
    )

    subjects = Subject.objects.all()
    classes = SchoolClass.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        homework.subject_id = request.POST["subject"]
        homework.school_class_id = request.POST["school_class"]
        homework.teacher_id = request.POST["teacher"]
        homework.title = request.POST["title"]
        homework.description = request.POST["description"]
        homework.due_date = request.POST["due_date"]

        if request.FILES.get("attachment"):
            homework.attachment = request.FILES["attachment"]

        homework.save()

        messages.success(
            request,
            "Homework updated successfully."
        )

        return redirect("homework_list")

    return render(
        request,
        "homework/edit_homework.html",
        {
            "homework": homework,
            "subjects": subjects,
            "classes": classes,
            "teachers": teachers,
        },
    )

@login_required
def delete_homework(request, pk):

    homework = get_object_or_404(
        Homework,
        pk=pk,
    )

    if request.method == "POST":

        homework.delete()

        messages.success(
            request,
            "Homework deleted successfully.",
        )

        return redirect("homework_list")

    return render(
        request,
        "homework/delete_homework.html",
        {
            "homework": homework,
        },
    )

@login_required
def parent_homework(request):

    children = Student.objects.filter(parent_user=request.user)

    classes = children.values_list(
        "school_class",
        flat=True
    )

    homework = Homework.objects.filter(
        school_class__in=classes
    ).order_by("-date_given")

    return render(
        request,
        "parents/homework.html",
        {
            "children": children,
            "homework": homework,
        },
    )

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def submit_homework(request, homework_id):

    student = Student.objects.get(user=request.user)

    homework = get_object_or_404(
        Homework,
        id=homework_id
    )

    submission = HomeworkSubmission.objects.filter(
        homework=homework,
        student=student
    ).first()

    if request.method == "POST":

        file = request.FILES.get("submission_file")

        if submission:

            submission.submission_file = file
            submission.save()

            messages.success(
                request,
                "Homework updated successfully."
            )

        else:

            HomeworkSubmission.objects.create(
                homework=homework,
                student=student,
                submission_file=file,
            )

            messages.success(
                request,
                "Homework submitted successfully."
            )

        return redirect("student_homework")

    return render(
        request,
        "students/submit_homework.html",
        {
            "homework": homework,
            "submission": submission,
        },
    )

@login_required
def homework_submissions(request, homework_id):

    homework = get_object_or_404(
        Homework,
        id=homework_id
    )

    submissions = HomeworkSubmission.objects.filter(
        homework=homework
    ).select_related(
        "student"
    )

    return render(
        request,
        "homework/homework_submissions.html",
        {
            "homework": homework,
            "submissions": submissions,
        },
    )


@login_required
def mark_homework(request, submission_id):

    submission = get_object_or_404(
        HomeworkSubmission,
        id=submission_id
    )

    teacher = Teacher.objects.filter(
        user=request.user
    ).first()

    if request.method == "POST":

        submission.marks = request.POST["marks"]
        submission.teacher_comment = request.POST["teacher_comment"]
        submission.graded_by = teacher
        submission.graded_at = timezone.now()

        submission.save()

        messages.success(
            request,
            "Homework marked successfully."
        )

        return redirect(
            "homework_submissions",
            submission.homework.id,
        )

    return render(
        request,
        "homework/mark_homework.html",
        {
            "submission": submission,
        },
    )