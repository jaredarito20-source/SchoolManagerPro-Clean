from django.shortcuts import render, redirect, get_object_or_404

from .models import Student, Teacher, Subject, SchoolClass


def home(request):
    context = {
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