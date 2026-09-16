from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from students.utils import get_user_school
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
                            HomeworkSubmission,
                           
)


from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from ..models import Homework, Subject, SchoolClass, Teacher




@login_required
def parent_dashboard(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    ).order_by(
        "first_name",
        "last_name",
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

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    ).order_by(
        "school_class",
        "first_name",
    )

    return render(
        request,
        "parents/parent_students.html",
        {
            "children": children,
        },
    )


@login_required
def parent_student_profile(request, student_id):

    school = request.user.school_user.school

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        parent_user=request.user,
    )

    marks = Mark.objects.filter(
        school=school,
        student=student,
    )

    fee_payments = FeePayment.objects.filter(
        school=school,
        student=student,
    )

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

@login_required
def parent_attendance(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    )

    attendance = Attendance.objects.filter(
        school=school,
        student__in=children,
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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
        school=school,
    )

    marks = (
        Mark.objects
        .filter(
            student=student,
            student__school=school,
        )
        .select_related(
            "subject",
            "exam",
        )
        .order_by(
            "exam__name",
            "subject__name",
        )
    )

    total = sum(
        mark.marks
        for mark in marks
    )

    count = marks.count()

    average = (
        round(total / count, 2)
        if count
        else 0
    )

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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
        school=school,
    )

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class,
        school_class__school=school,
    ).first()

    payments = FeePayment.objects.filter(
        student=student,
        student__school=school,
    ).order_by("-payment_date")

    total_paid = sum(
        payment.amount_paid
        for payment in payments
    )

    total_fee = (
        fee_structure.total_fee
        if fee_structure
        else 0
    )

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

    school = request.user.school_user.school

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        parent_user=request.user,
    )

    fee_structure = (
        FeeStructure.objects
        .filter(
            school=school,
            school_class=student.school_class,
        )
        .first()
    )

    payments = (
        FeePayment.objects
        .filter(
            school=school,
            student=student,
        )
        .order_by("-payment_date")
    )

    total_paid = sum(
        payment.amount_paid
        for payment in payments
    )

    total_fee = (
        fee_structure.total_fee
        if fee_structure
        else 0
    )

    balance = total_fee - total_paid

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="Fee_Statement_'
        f'{student.admission_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>FEE STATEMENT</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            f"Student: {student.first_name} "
            f"{student.last_name}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Admission No: {student.admission_number}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Class: {student.school_class}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "<br/>",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Fees: Ksh {total_fee}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Paid: Ksh {total_paid}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Balance: Ksh {balance}",
            styles["Normal"],
        )
    )

    doc.build(story)

    return response
@login_required
def parent_fee_balance(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    children = Student.objects.filter(
        parent_user=request.user,
        school=school,
    ).select_related(
        "school_class",
    )

    fee_data = []

    for child in children:

        fee_structure = FeeStructure.objects.filter(
            school_class=child.school_class,
            school_class__school=school,
        ).first()

        total_fee = (
            fee_structure.total_fee
            if fee_structure
            else 0
        )

        payments = FeePayment.objects.filter(
            student=child,
            student__school=school,
        )

        total_paid = sum(
            payment.amount_paid
            for payment in payments
        )

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

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    )

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

    student = children.filter(
        id=child_id
    ).first()

    if student is None:
        student = children.first()
        request.session["selected_child"] = student.id

    attendance = Attendance.objects.filter(
        school=school,
        student=student,
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
    school = get_user_school(user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )

        return redirect("home")

    # Administrator
    if (
        user.is_superuser
        or user.groups.filter(
            name="Administrators"
        ).exists()
    ):

        homework = Homework.objects.filter(
            school=school
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by(
            "-date_given"
        )

    # Teacher
    elif user.groups.filter(
        name="Teachers"
    ).exists():

        teacher = Teacher.objects.filter(
            user=user,
            school=school,
        ).first()

        if teacher:

            homework = Homework.objects.filter(
                school=school,
                teacher=teacher,
            ).select_related(
                "subject",
                "school_class",
                "teacher",
            ).order_by(
                "-date_given"
            )

        else:
            homework = Homework.objects.none()

    # Parent
    elif user.groups.filter(
        name="Parents"
    ).exists():

        children = Student.objects.filter(
            parent_user=user,
            school=school,
        )

        classes = children.values_list(
            "school_class_id",
            flat=True,
        )

        homework = Homework.objects.filter(
            school=school,
            school_class_id__in=classes,
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by(
            "-date_given"
        )

    # Student
    else:

        student = Student.objects.filter(
            user=user,
            school=school,
        ).first()

        if student:

            homework = Homework.objects.filter(
                school=school,
                school_class=student.school_class,
            ).select_related(
                "subject",
                "school_class",
                "teacher",
            ).order_by(
                "-date_given"
            )

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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    subjects = Subject.objects.filter(
        school=school
    ).select_related(
        "school_class",
        "teacher",
    )

    classes = SchoolClass.objects.filter(
        school=school
    )

    teachers = Teacher.objects.filter(
        school=school
    )

    if request.method == "POST":

        try:

            subject = Subject.objects.get(
                id=request.POST["subject"],
                school=school,
            )

            school_class = SchoolClass.objects.get(
                id=request.POST["school_class"],
                school=school,
            )

            teacher = Teacher.objects.get(
                id=request.POST["teacher"],
                school=school,
            )

        except (
            Subject.DoesNotExist,
            SchoolClass.DoesNotExist,
            Teacher.DoesNotExist,
        ):

            messages.error(
                request,
                "Invalid subject, class, or teacher."
            )

            return render(
                request,
                "homework/add_homework.html",
                {
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        # If the subject is assigned to a specific class,
        # make sure it matches the selected class.
        if (
            subject.school_class
            and subject.school_class_id != school_class.id
        ):

            messages.error(
                request,
                "The selected subject does not belong to the selected class."
            )

            return render(
                request,
                "homework/add_homework.html",
                {
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        Homework.objects.create(
            school=school,
            subject=subject,
            school_class=school_class,
            teacher=teacher,
            title=request.POST["title"],
            description=request.POST["description"],
            due_date=request.POST["due_date"],
            attachment=request.FILES.get("attachment"),
        )

        messages.success(
            request,
            "Homework added successfully."
        )

        return redirect("students:homework_list")

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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "subject",
            "school_class",
            "teacher",
        ),
        pk=pk,
        school=school,
    )

    subjects = Subject.objects.filter(
        school=school
    )

    classes = SchoolClass.objects.filter(
        school=school
    )

    teachers = Teacher.objects.filter(
        school=school
    )

    if request.method == "POST":

        try:

            subject = Subject.objects.get(
                id=request.POST["subject"],
                school=school,
            )

            school_class = SchoolClass.objects.get(
                id=request.POST["school_class"],
                school=school,
            )

            teacher = Teacher.objects.get(
                id=request.POST["teacher"],
                school=school,
            )

        except (
            Subject.DoesNotExist,
            SchoolClass.DoesNotExist,
            Teacher.DoesNotExist,
        ):

            messages.error(
                request,
                "Invalid subject, class, or teacher."
            )

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

        if (
            subject.school_class
            and subject.school_class_id != school_class.id
        ):

            messages.error(
                request,
                "The selected subject does not belong to the selected class."
            )

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

        homework.subject = subject
        homework.school_class = school_class
        homework.teacher = teacher
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

        return redirect("students:homework_list")

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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    homework = get_object_or_404(
        Homework,
        pk=pk,
        school=school,
    )

    if request.method == "POST":

        homework.delete()

        messages.success(
            request,
            "Homework deleted successfully."
        )

        return redirect("students:homework_list")

    return render(
        request,
        "homework/delete_homework.html",
        {
            "homework": homework,
        },
    )

@login_required
def parent_homework(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    children = Student.objects.filter(
        parent_user=request.user,
        school=school,
    ).select_related(
        "school_class"
    )

    classes = children.values_list(
        "school_class_id",
        flat=True,
    )

    homework = Homework.objects.filter(
        school=school,
        school_class_id__in=classes,
    ).select_related(
        "subject",
        "school_class",
        "teacher",
    ).order_by(
        "-date_given"
    )

    return render(
        request,
        "parents/homework.html",
        {
            "children": children,
            "homework": homework,
        },
    )

@login_required
def submit_homework(request, homework_id):

    student = Student.objects.filter(
        user=request.user
    ).select_related(
        "school",
        "school_class",
    ).first()

    if not student:
        messages.error(
            request,
            "Student profile not found."
        )
        return redirect("home")

    if not student.school:
        messages.error(
            request,
            "Your student account is not associated with a school."
        )
        return redirect("home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "school",
            "school_class",
            "subject",
            "teacher",
        ),
        id=homework_id,
        school=student.school,
        school_class=student.school_class,
    )

    submission = HomeworkSubmission.objects.filter(
        homework=homework,
        student=student,
    ).first()

    if request.method == "POST":

        file = request.FILES.get(
            "submission_file"
        )

        if submission:

            if file:
                submission.submission_file = file

            submission.save()

            messages.success(
                request,
                "Homework updated successfully."
            )

        else:

            if not file:
                messages.error(
                    request,
                    "Please select a file to submit."
                )

                return render(
                    request,
                    "students/submit_homework.html",
                    {
                        "homework": homework,
                        "submission": submission,
                    },
                )

            HomeworkSubmission.objects.create(
                homework=homework,
                student=student,
                submission_file=file,
            )

            messages.success(
                request,
                "Homework submitted successfully."
            )

        return redirect(
            "student_homework"
        )

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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "school",
            "teacher",
            "school_class",
            "subject",
        ),
        id=homework_id,
        school=school,
    )

    user = request.user

    # Teachers can only view submissions
    # for their own homework.
    if user.groups.filter(
        name="Teachers"
    ).exists():

        teacher = Teacher.objects.filter(
            user=user,
            school=school,
        ).first()

        if not teacher or homework.teacher_id != teacher.id:
            messages.error(
                request,
                "You are not allowed to view these submissions."
            )
            return redirect("students:homework_list")

    submissions = HomeworkSubmission.objects.filter(
        homework=homework,
        student__school=school,
    ).select_related(
        "student",
        "graded_by",
    ).order_by(
        "-submitted_at"
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

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")
    
    submission = get_object_or_404(
        HomeworkSubmission.objects.select_related(
            "homework",
            "homework__teacher",
            "homework__school",
            "student",
            "student__school",
        ),
        id=submission_id,
        homework__school=school,
        student__school=school,
    )

    user = request.user

    # Find teacher
    teacher = Teacher.objects.filter(
        user=user,
        school=school,
    ).first()

    # Teacher permission
    if user.groups.filter(
        name="Teachers"
    ).exists():

        if not teacher:
            messages.error(
                request,
                "Teacher profile not found."
            )
            return redirect("students:homework_list")

        if submission.homework.teacher_id != teacher.id:
            messages.error(
                request,
                "You are not allowed to mark this homework."
            )
            return redirect(
                "homework_submissions",
                submission.homework.id,
            )

    # Administrator or authorized teacher
    if request.method == "POST":

        marks_value = request.POST.get(
            "marks"
        )

        teacher_comment = request.POST.get(
            "teacher_comment",
            "",
        )

        if marks_value:
            try:
                marks = float(marks_value)

            except (TypeError, ValueError):

                messages.error(
                    request,
                    "Please enter valid marks."
                )

                return render(
                    request,
                    "homework/mark_homework.html",
                    {
                        "submission": submission,
                    },
                )

            if marks < 0 or marks > 100:

                messages.error(
                    request,
                    "Marks must be between 0 and 100."
                )

                return render(
                    request,
                    "homework/mark_homework.html",
                    {
                        "submission": submission,
                    },
                )

            submission.marks = marks

        else:
            submission.marks = None

        submission.teacher_comment = teacher_comment
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