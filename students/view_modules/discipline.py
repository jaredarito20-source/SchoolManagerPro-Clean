from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from students.utils import get_user_school

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

    school = get_user_school(request.user)

    cases = DisciplineCase.objects.filter(
        school=school
    ).select_related(
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

    school = get_user_school(request.user)

    students = Student.objects.filter(
        school=school
    ).select_related(
        "school_class"
    ).order_by(
        "first_name",
        "last_name",
    )

    categories = DisciplineCategory.objects.filter(
        school=school
    ).order_by(
        "name"
    )

    teachers = Teacher.objects.filter(
        school=school
    ).order_by(
        "first_name",
        "last_name",
    )

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"],
            school=school,
        )

        category = get_object_or_404(
            DisciplineCategory,
            id=request.POST["category"],
            school=school,
        )

        teacher = get_object_or_404(
            Teacher,
            id=request.POST["reported_by"],
            school=school,
        )

        DisciplineCase.objects.create(

            school=school,

            student=student,

            category=category,

            reported_by=teacher,

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
            "students:discipline_case_list"
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

    school = get_user_school(request.user)

    case = get_object_or_404(
        DisciplineCase,
        id=id,
        school=school,
    )

    students = Student.objects.filter(
        school=school
    ).select_related(
        "school_class"
    ).order_by(
        "first_name",
        "last_name",
    )

    categories = DisciplineCategory.objects.filter(
        school=school
    ).order_by(
        "name"
    )

    teachers = Teacher.objects.filter(
        school=school
    ).order_by(
        "first_name",
        "last_name",
    )

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"],
            school=school,
        )

        category = get_object_or_404(
            DisciplineCategory,
            id=request.POST["category"],
            school=school,
        )

        teacher = get_object_or_404(
            Teacher,
            id=request.POST["reported_by"],
            school=school,
        )

        case.student = student
        case.category = category
        case.reported_by = teacher

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
            "students:discipline_case_list"
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

    school = get_user_school(request.user)

    case = get_object_or_404(
        DisciplineCase,
        id=id,
        school=school,
    )

    if request.method == "POST":

        case.delete()

        messages.success(
            request,
            "Discipline case deleted successfully."
        )

        return redirect(
            "students:discipline_case_list"
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

    school = get_user_school(request.user)

    case = get_object_or_404(
        DisciplineCase.objects.select_related(
            "student",
            "student__school_class",
            "category",
            "reported_by",
            "school",
        ),
        id=id,
        school=school,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Discipline_Case_'
        f'{case.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "DISCIPLINE CASE REPORT",
    )

    y = 690

    p.drawString(
        50,
        y,
        f"Admission No : {case.student.admission_number}"
    )
    y -= 20

    p.drawString(
        50,
        y,
        f"Student : {case.student.first_name} "
        f"{case.student.last_name}",
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

    p.setFont(
        "Helvetica-Bold",
        11,
    )

    p.drawString(
        50,
        y,
        "Description",
    )

    y -= 20

    p.setFont(
        "Helvetica",
        10,
    )

    text = p.beginText(
        50,
        y,
    )

    for line in case.description.splitlines():
        text.textLine(line)

    p.drawText(text)

    y = text.getY() - 30

    p.setFont(
        "Helvetica-Bold",
        11,
    )

    p.drawString(
        50,
        y,
        "Action Taken",
    )

    y -= 20

    p.setFont(
        "Helvetica",
        10,
    )

    text = p.beginText(
        50,
        y,
    )

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

    school = get_user_school(request.user)

    categories = DisciplineCategory.objects.filter(
        school=school
    ).order_by("name")

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

    school = get_user_school(request.user)

    category = get_object_or_404(
        DisciplineCategory,
        id=id,
        school=school,
    )

    if request.method == "POST":

        category.name = request.POST["name"]

        category.description = request.POST["description"]

        category.save()

        messages.success(
            request,
            "Discipline category updated successfully."
        )

        return redirect(
            "students:discipline_category_list"
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

    school = get_user_school(request.user)

    category = get_object_or_404(
        DisciplineCategory,
        id=id,
        school=school,
    )

    if request.method == "POST":

        category.delete()

        messages.success(
            request,
            "Discipline category deleted successfully."
        )

        return redirect(
            "students:discipline_category_list"
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

    school = get_user_school(request.user)

    if request.method == "POST":

        DisciplineCategory.objects.create(
            school=school,

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
            "students:discipline_category_list",
        )

    return render(
        request,
        "students/add_discipline_category.html",
    )

@login_required
@admin_or_bursar
def discipline_dashboard(request):

    school = get_user_school(request.user)

    # All discipline cases for this school
    cases = DisciplineCase.objects.filter(
        school=school
    )

    # Basic statistics
    total_cases = cases.count()

    open_cases = cases.filter(
        status="Open"
    ).count()

    closed_cases = cases.filter(
        status="Closed"
    ).count()

    # Categories belonging to this school
    total_categories = DisciplineCategory.objects.filter(
        school=school
    ).count()

    # Students belonging to this school
    total_students = Student.objects.filter(
        school=school
    ).count()

    # Cases by category
    category_summary = (
        DisciplineCategory.objects
        .filter(school=school)
        .annotate(
            total_cases=Count(
                "disciplinecase"
            )
        )
        .order_by("-total_cases")
    )

    # Cases by class
    class_summary = (
        SchoolClass.objects
        .filter(school=school)
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

    school = get_user_school(request.user)

    # --------------------------------------------------
    # SCHOOL-FILTERED DATA
    # --------------------------------------------------

    cases = DisciplineCase.objects.filter(
        school=school
    )

    total_cases = cases.count()

    open_cases = cases.filter(
        status="Open"
    ).count()

    closed_cases = cases.filter(
        status="Closed"
    ).count()

    total_categories = DisciplineCategory.objects.filter(
        school=school
    ).count()

    total_students = Student.objects.filter(
        school=school
    ).count()

    category_summary = (
        DisciplineCategory.objects
        .filter(
            school=school
        )
        .annotate(
            total_cases=Count(
                "disciplinecase"
            )
        )
        .order_by("-total_cases")
    )

    class_summary = (
        SchoolClass.objects
        .filter(
            school=school
        )
        .annotate(
            total_cases=Count(
                "students__discipline_cases"
            )
        )
        .order_by("-total_cases")
    )

    # --------------------------------------------------
    # PDF RESPONSE
    # --------------------------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="Discipline_Dashboard.pdf"'
    )

    p = canvas.Canvas(response)

    # --------------------------------------------------
    # SCHOOL HEADER
    # --------------------------------------------------

    draw_school_header(
        p,
        "DISCIPLINE DASHBOARD REPORT",
        school,
    )
    y = 710

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    p.setFont(
        "Helvetica-Bold",
        13,
    )

    p.drawString(
        50,
        y,
        "SUMMARY",
    )

    y -= 30

    p.setFont(
        "Helvetica",
        11,
    )

    p.drawString(
        60,
        y,
        f"Total Discipline Cases : {total_cases}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Open Cases             : {open_cases}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Closed Cases           : {closed_cases}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Discipline Categories  : {total_categories}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Total Students         : {total_students}",
    )

    # --------------------------------------------------
    # CASES BY CATEGORY
    # --------------------------------------------------

    y -= 45

    p.setFont(
        "Helvetica-Bold",
        13,
    )

    p.drawString(
        50,
        y,
        "CASES BY CATEGORY",
    )

    y -= 25

    p.setFont(
        "Helvetica-Bold",
        11,
    )

    p.drawString(
        60,
        y,
        "No",
    )

    p.drawString(
        110,
        y,
        "Category",
    )

    p.drawRightString(
        520,
        y,
        "Cases",
    )

    y -= 8

    p.line(
        50,
        y,
        530,
        y,
    )

    y -= 18

    p.setFont(
        "Helvetica",
        10,
    )

    for i, category in enumerate(
        category_summary,
        start=1,
    ):

        p.drawString(
            60,
            y,
            str(i),
        )

        p.drawString(
            110,
            y,
            category.name,
        )

        p.drawRightString(
            520,
            y,
            str(category.total_cases),
        )

        y -= 18

        if y < 120:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "DISCIPLINE DASHBOARD REPORT",
            )

            y = 720

            p.setFont(
                "Helvetica",
                10,
            )

    # --------------------------------------------------
    # CASES BY CLASS
    # --------------------------------------------------

    y -= 25

    p.setFont(
        "Helvetica-Bold",
        13,
    )

    p.drawString(
        50,
        y,
        "CASES BY CLASS",
    )

    y -= 25

    p.setFont(
        "Helvetica-Bold",
        11,
    )

    p.drawString(
        60,
        y,
        "No",
    )

    p.drawString(
        110,
        y,
        "Class",
    )

    p.drawRightString(
        520,
        y,
        "Cases",
    )

    y -= 8

    p.line(
        50,
        y,
        530,
        y,
    )

    y -= 18

    p.setFont(
        "Helvetica",
        10,
    )

    for i, school_class in enumerate(
        class_summary,
        start=1,
    ):

        p.drawString(
            60,
            y,
            str(i),
        )

        p.drawString(
            110,
            y,
            school_class.name,
        )

        p.drawRightString(
            520,
            y,
            str(school_class.total_cases),
        )

        y -= 18

        if y < 80:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "DISCIPLINE DASHBOARD REPORT",
            )

            y = 720

            p.setFont(
                "Helvetica",
                10,
            )

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response