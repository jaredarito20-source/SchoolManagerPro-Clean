from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from students.models import *
from students.models import (
    Student,
    SchoolClass,
    DisciplineCase,
    DisciplineCategory,
)

from students.decorators import admin_or_bursar
from students.utils import draw_school_header, draw_school_footer


@login_required
@admin_or_bursar
def discipline_case_list(request):

    cases = DisciplineCase.objects.select_related(
        "student",
        "student__school_class",
        "category",
        "reported_by",
    ).order_by("-incident_date")

    return render(
        request,
        "students/discipline_case_list.html",
        {
            "cases": cases,
        },
    )

@login_required
@admin_or_bursar
def add_discipline_case(request):

    students = Student.objects.select_related(
        "school_class"
    )

    categories = DisciplineCategory.objects.all()

    teachers = Teacher.objects.all()

    if request.method == "POST":

        DisciplineCase.objects.create(

            student=Student.objects.get(
                id=request.POST["student"]
            ),

            category=DisciplineCategory.objects.get(
                id=request.POST["category"]
            ),

            reported_by=Teacher.objects.get(
                id=request.POST["reported_by"]
            ),

            incident_date=request.POST["incident_date"],

            description=request.POST["description"],

            action_taken=request.POST["action_taken"],

            status=request.POST["status"],

        )

        messages.success(
            request,
            "Discipline case recorded successfully."
        )

        return redirect(
            "discipline_case_list"
        )

    return render(
        request,
        "students/add_discipline_case.html",
        {
            "students": students,
            "categories": categories,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def edit_discipline_case(request, id):

    case = get_object_or_404(
        DisciplineCase,
        id=id,
    )

    students = Student.objects.select_related(
        "school_class"
    )

    categories = DisciplineCategory.objects.all()

    teachers = Teacher.objects.all()

    if request.method == "POST":

        case.student = Student.objects.get(
            id=request.POST["student"]
        )

        case.category = DisciplineCategory.objects.get(
            id=request.POST["category"]
        )

        case.reported_by = Teacher.objects.get(
            id=request.POST["reported_by"]
        )

        case.incident_date = request.POST["incident_date"]

        case.description = request.POST["description"]

        case.action_taken = request.POST["action_taken"]

        case.status = request.POST["status"]

        case.save()

        messages.success(
            request,
            "Discipline case updated successfully."
        )

        return redirect(
            "discipline_case_list"
        )

    return render(
        request,
        "students/edit_discipline_case.html",
        {
            "case": case,
            "students": students,
            "categories": categories,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def delete_discipline_case(request, id):

    case = get_object_or_404(
        DisciplineCase,
        id=id,
    )

    if request.method == "POST":

        case.delete()

        messages.success(
            request,
            "Discipline case deleted successfully."
        )

        return redirect(
            "discipline_case_list"
        )

    return render(
        request,
        "students/delete_discipline_case.html",
        {
            "case": case,
        },
    )

@login_required
@admin_or_bursar
def print_discipline_case(request, id):

    case = get_object_or_404(
        DisciplineCase.objects.select_related(
            "student",
            "student__school_class",
            "category",
            "reported_by",
        ),
        id=id,
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="Discipline_Case_{case.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "DISCIPLINE CASE REPORT",
    )

    y = 690

    p.drawString(50, y, f"Admission No : {case.student.admission_number}")
    y -= 20

    p.drawString(
        50,
        y,
        f"Student : {case.student.first_name} {case.student.last_name}",
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Class : {case.student.school_class}",
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Category : {case.category}",
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Reported By : {case.reported_by}",
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Incident Date : {case.incident_date}",
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Status : {case.status}",
    )

    y -= 40

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Description")

    y -= 20

    p.setFont("Helvetica", 10)

    text = p.beginText(50, y)

    for line in case.description.splitlines():
        text.textLine(line)

    p.drawText(text)

    y = text.getY() - 30

    p.setFont("Helvetica-Bold", 11)

    p.drawString(50, y, "Action Taken")

    y -= 20

    p.setFont("Helvetica", 10)

    text = p.beginText(50, y)

    for line in case.action_taken.splitlines():
        text.textLine(line)

    p.drawText(text)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def discipline_category_list(request):

    categories = DisciplineCategory.objects.all()

    return render(
        request,
        "students/discipline_category_list.html",
        {
            "categories": categories,
        },
    )

@login_required
@admin_or_bursar
def edit_discipline_category(request, id):

    category = get_object_or_404(
        DisciplineCategory,
        id=id,
    )

    if request.method == "POST":

        category.name = request.POST["name"]

        category.description = request.POST["description"]

        category.active = "active" in request.POST

        category.save()

        return redirect(
            "discipline_category_list"
        )

    return render(
        request,
        "students/edit_discipline_category.html",
        {
            "category": category,
        },
    )

@login_required
@admin_or_bursar
def delete_discipline_category(request, id):

    category = get_object_or_404(
        DisciplineCategory,
        id=id,
    )

    if request.method == "POST":

        category.delete()

        return redirect(
            "discipline_category_list"
        )

    return render(
        request,
        "students/delete_discipline_category.html",
        {
            "category": category,
        },
    )

@login_required
@admin_or_bursar
def add_discipline_category(request):

    if request.method == "POST":

        DisciplineCategory.objects.create(

            name=request.POST["name"],

            description=request.POST.get(
                "description",
                "",
            ),

        )

        messages.success(
            request,
            "Discipline category added successfully.",
        )

        return redirect(
            "discipline_category_list",
        )

    return render(
        request,
        "students/add_discipline_category.html",
    )

@login_required
@admin_or_bursar
def discipline_dashboard(request):

    total_cases = DisciplineCase.objects.count()

    open_cases = DisciplineCase.objects.filter(
        status="Open"
    ).count()

    closed_cases = DisciplineCase.objects.filter(
        status="Closed"
    ).count()

    total_categories = DisciplineCategory.objects.count()

    total_students = Student.objects.count()

    category_summary = (
        DisciplineCategory.objects
        .annotate(
            total_cases=Count("disciplinecase")
        )
        .order_by("-total_cases")
    )

    class_summary = (
        SchoolClass.objects
        .annotate(
            total_cases=Count(
                "students__discipline_cases"
            )
        )
        .order_by("-total_cases")
)
    return render(
        request,
        "students/discipline_dashboard.html",
        {
            "total_cases": total_cases,
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "total_categories": total_categories,
            "total_students": total_students,
            "category_summary": category_summary,
            "class_summary": class_summary,
        },
    )




@login_required
@admin_or_bursar
def print_discipline_dashboard(request):

    total_cases = DisciplineCase.objects.count()

    open_cases = DisciplineCase.objects.filter(
        status="Open"
    ).count()

    closed_cases = DisciplineCase.objects.filter(
        status="Closed"
    ).count()

    total_categories = DisciplineCategory.objects.count()

    total_students = Student.objects.count()

    category_summary = (
        DisciplineCategory.objects
        .annotate(total_cases=Count("disciplinecase"))
        .order_by("-total_cases")
    )

    class_summary = (
        SchoolClass.objects
        .annotate(
            total_cases=Count("students__discipline_cases")
        )
        .order_by("-total_cases")
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="Discipline_Dashboard.pdf"'
    )

    p = canvas.Canvas(response)

    # School Header
    draw_school_header(
        p,
        "DISCIPLINE DASHBOARD REPORT",
    )

    y = 710

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "SUMMARY")
    y -= 30

    p.setFont("Helvetica", 11)

    p.drawString(60, y, f"Total Discipline Cases : {total_cases}")
    y -= 20

    p.drawString(60, y, f"Open Cases             : {open_cases}")
    y -= 20

    p.drawString(60, y, f"Closed Cases           : {closed_cases}")
    y -= 20

    p.drawString(60, y, f"Discipline Categories  : {total_categories}")
    y -= 20

    p.drawString(60, y, f"Total Students         : {total_students}")

    # --------------------------------------------------

    y -= 45

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        50,
        y,
        "CASES BY CATEGORY",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 11)

    p.drawString(60, y, "No")

    p.drawString(110, y, "Category")

    p.drawRightString(520, y, "Cases")

    y -= 8

    p.line(50, y, 530, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for i, category in enumerate(category_summary, start=1):

        p.drawString(60, y, str(i))

        p.drawString(110, y, category.name)

        p.drawRightString(
            520,
            y,
            str(category.total_cases),
        )

        y -= 18

        if y < 120:

            p.showPage()

            draw_school_header(
                p,
                "DISCIPLINE DASHBOARD REPORT",
            )

            y = 720

            p.setFont("Helvetica", 10)

    # --------------------------------------------------

    y -= 25

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        50,
        y,
        "CASES BY CLASS",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 11)

    p.drawString(60, y, "No")

    p.drawString(110, y, "Class")

    p.drawRightString(520, y, "Cases")

    y -= 8

    p.line(50, y, 530, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for i, school_class in enumerate(class_summary, start=1):

        p.drawString(60, y, str(i))

        p.drawString(110, y, school_class.name)

        p.drawRightString(
            520,
            y,
            str(school_class.total_cases),
        )

        y -= 18

        if y < 80:

            p.showPage()

            draw_school_header(
                p,
                "DISCIPLINE DASHBOARD REPORT",
            )

            y = 720

            p.setFont("Helvetica", 10)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

# medication



