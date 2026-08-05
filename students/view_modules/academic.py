from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
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
@admin_or_bursar
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
@admin_or_bursar
def student_list(request):
    students = Student.objects.all()
    return render(request, "students/student_list.html", {
        "students": students
    })

@login_required
@admin_or_bursar
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
@admin_or_bursar
def class_list(request):
    classes = SchoolClass.objects.all()
    return render(request, "students/class_list.html", {
        "classes": classes
    })

@login_required
@admin_or_bursar
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
@admin_or_bursar
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
@admin_or_bursar
def delete_class(request, id):
    school_class = get_object_or_404(SchoolClass, id=id)

    if request.method == "POST":
        school_class.delete()
        return redirect("class_list")

    return render(request, "students/delete_class.html", {
        "school_class": school_class
    })

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
@admin_or_bursar
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



