from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Teacher, Subject, SchoolClass, Exam, Mark
from django.db.models import Sum, Avg


from .models import Student, Teacher, Subject, SchoolClass, SchoolProfile

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

def student_list(request):
    students = Student.objects.all()
    return render(request, "students/student_list.html", {
        "students": students
    })


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

def delete_student(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == "POST":
        student.delete()
        return redirect("student_list")

    return render(request, "students/delete_student.html", {
        "student": student
    })
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, "students/teacher_list.html", {
        "teachers": teachers
    })
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

def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)

    if request.method == "POST":
        teacher.delete()
        return redirect("teacher_list")

    return render(request, "students/delete_teacher.html", {
        "teacher": teacher
    })

def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "students/subject_list.html", {
        "subjects": subjects
    })


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


def delete_subject(request, id):
    subject = get_object_or_404(Subject, id=id)

    if request.method == "POST":
        subject.delete()
        return redirect("subject_list")

    return render(request, "students/delete_subject.html", {
        "subject": subject
    })

def class_list(request):
    classes = SchoolClass.objects.all()
    return render(request, "students/class_list.html", {
        "classes": classes
    })


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

def exam_list(request):
    exams = Exam.objects.all()

    return render(request, "students/exam_list.html", {
        "exams": exams
    })


def add_exam(request):
    if request.method == "POST":
        Exam.objects.create(
            name=request.POST["name"],
            term=request.POST["term"],
            year=request.POST["year"],
        )

        return redirect("exam_list")

    return render(request, "students/add_exam.html")


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

def mark_list(request):
    marks = Mark.objects.all()

    return render(request, "students/mark_list.html", {
        "marks": marks
    })


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