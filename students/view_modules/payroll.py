from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from reportlab.lib import colors
from datetime import date
from reportlab.lib.units import inch
from django.utils import timezone

import uuid
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib.pagesizes import A4
from django.http import FileResponse
from students.models import (
    Student,
    SchoolClass,
    FeeStructure,
    FeePayment,
    MedicalVisit,
    Medication,
    Prescription,
    SchoolProfile,
    SalaryStructure,
    Payroll,
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)


from reportlab.pdfgen import canvas

from students.models import (
    Student,
    SchoolClass,
    FeeStructure,
    FeePayment,
    SchoolProfile,
    Teacher,
)

from students.decorators import (
    admin_or_bursar,
    in_group,
)

from students.utils import (
    draw_school_header,
    draw_school_footer,
)


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
)
def salary_structure_list(request):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        salaries = SalaryStructure.objects.select_related(
            "teacher",
            "teacher__school",
        ).all().order_by(
            "teacher__first_name",
            "teacher__last_name",
        )

    # -----------------------------------------
    # NORMAL SCHOOL USER
    # -----------------------------------------
    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

        salaries = SalaryStructure.objects.select_related(
            "teacher",
            "teacher__school",
        ).filter(
            teacher__school=school
        ).order_by(
            "teacher__first_name",
            "teacher__last_name",
        )

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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        teachers = Teacher.objects.select_related(
            "school"
        ).all().order_by(
            "first_name",
            "last_name",
        )

    # -----------------------------------------
    # NORMAL SCHOOL USER
    # -----------------------------------------
    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

        teachers = Teacher.objects.filter(
            school=school
        ).order_by(
            "first_name",
            "last_name",
        )

    # -----------------------------------------
    # SAVE
    # -----------------------------------------
    if request.method == "POST":

        teacher = get_object_or_404(
            Teacher,
            id=request.POST["teacher"],
        )

        # -------------------------------------
        # SECURITY CHECK
        # -------------------------------------

        if not request.user.is_superuser:

            if teacher.school_id != school.id:

                messages.error(
                    request,
                    "You cannot create a salary structure "
                    "for a teacher from another school."
                )

                return redirect("students:salary_structure_list")

        SalaryStructure.objects.create(

            teacher=teacher,

            basic_salary=request.POST[
                "basic_salary"
            ],

            house_allowance=request.POST[
                "house_allowance"
            ],

            medical_allowance=request.POST[
                "medical_allowance"
            ],

            transport_allowance=request.POST[
                "transport_allowance"
            ],

            other_allowance=request.POST[
                "other_allowance"
            ],

            paye=request.POST[
                "paye"
            ],

            sha=request.POST[
                "sha"
            ],

            nssf=request.POST[
                "nssf"
            ],

            other_deductions=request.POST.get(
                "other_deductions",
                0,
            ),

            bank_name=request.POST.get(
                "bank_name",
                "",
            ),

            account_number=request.POST.get(
                "account_number",
                "",
            ),
        )

        messages.success(
            request,
            "Salary structure added successfully."
        )

        return redirect("students:salary_structure_list")

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

        return redirect("students:salary_structure_list")

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

        return redirect("students:salary_structure_list")

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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        school = None

    # -----------------------------------------
    # NORMAL SCHOOL USER
    # -----------------------------------------
    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

    # -----------------------------------------
    # GENERATE PAYROLL
    # -----------------------------------------
    if request.method == "POST":

        month = request.POST.get("month")
        year = int(request.POST.get("year"))

        # -------------------------------------
        # SUPERUSER
        # -------------------------------------
        if request.user.is_superuser:

            school_id = request.POST.get("school")

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect("generate_payroll")

            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        # -------------------------------------
        # SALARY STRUCTURES
        # -------------------------------------

        salary_structures = SalaryStructure.objects.select_related(
            "teacher"
        )

        # -------------------------------------
        # FILTER BY SCHOOL
        # -------------------------------------

        if school:

            salary_structures = salary_structures.filter(
                teacher__school=school
            )

        # -------------------------------------
        # GENERATE EACH PAYROLL
        # -------------------------------------

        for salary in salary_structures:

            teacher = salary.teacher

            # ---------------------------------
            # SAFETY CHECK
            # ---------------------------------

            if not teacher.school:

                continue

            # ---------------------------------
            # PREVENT DUPLICATE PAYROLL
            # ---------------------------------

            if Payroll.objects.filter(
                teacher=teacher,
                month=month,
                year=year,
            ).exists():

                continue

            # ---------------------------------
            # SALARY CALCULATIONS
            # ---------------------------------

            gross_salary = salary.gross_salary()

            deductions = (
                salary.paye
                + salary.sha
                + salary.nssf
                + salary.other_deductions
            )

            net_salary = (
                gross_salary
                - deductions
            )

            # ---------------------------------
            # CREATE PAYROLL
            # ---------------------------------

            Payroll.objects.create(

                school=teacher.school,

                teacher=teacher,

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

        messages.success(
            request,
            f"Payroll for {month} {year} generated successfully."
        )

        return redirect("students:payroll_list")

    # -----------------------------------------
    # SCHOOLS FOR SUPERUSER
    # -----------------------------------------

    schools = []

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

    # -----------------------------------------
    # CALENDAR YEARS
    # -----------------------------------------

    current_year = timezone.now().year

    if request.user.is_superuser:

        existing_years = (
            Payroll.objects
            .values_list(
                "year",
                flat=True,
            )
            .distinct()
        )

    else:

        existing_years = (
            Payroll.objects
            .filter(
                school=school
            )
            .values_list(
                "year",
                flat=True,
            )
            .distinct()
        )

    calendar_years = {
        int(year)
        for year in existing_years
        if year
    }

    # Always make the current calendar year available.
    calendar_years.add(current_year)

    calendar_years = sorted(
        calendar_years,
        reverse=True,
    )

    return render(
        request,
        "students/generate_payroll.html",
        {
            "schools": schools,
            "calendar_years": calendar_years,
        },
    )
@login_required
@admin_or_bursar
def payroll_list(request):


    # -----------------------------------------
    # DETERMINE SCHOOL ACCESS
    # -----------------------------------------

    if request.user.is_superuser:

        school = None

    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

    # -----------------------------------------
    # BASE PAYROLL QUERYSET
    # -----------------------------------------

    payrolls = Payroll.objects.select_related(
        "teacher",
        "school",
    )

    # -----------------------------------------
    # SCHOOL FILTER
    # -----------------------------------------

    if school:

        payrolls = payrolls.filter(
            school=school
        )

    # -----------------------------------------
    # FILTER VALUES
    # -----------------------------------------

    selected_year = request.GET.get("year", "")
    selected_month = request.GET.get("month", "")

    # -----------------------------------------
    # FILTER BY CALENDAR YEAR
    # -----------------------------------------

    if selected_year:

        try:

            selected_year = int(selected_year)

            payrolls = payrolls.filter(
                year=selected_year
            )

        except (TypeError, ValueError):

            selected_year = ""

    # -----------------------------------------
    # FILTER BY MONTH
    # -----------------------------------------

    if selected_month:

        payrolls = payrolls.filter(
            month=selected_month
        )

    # -----------------------------------------
    # CALENDAR YEARS
    # -----------------------------------------

    if school:

        existing_years = (
            Payroll.objects
            .filter(
                school=school
            )
            .values_list(
                "year",
                flat=True,
            )
            .distinct()
        )

    else:

        existing_years = (
            Payroll.objects
            .values_list(
                "year",
                flat=True,
            )
            .distinct()
        )

    calendar_years = sorted(
        {
            int(year)
            for year in existing_years
            if year
        },
        reverse=True,
    )

    # -----------------------------------------
    # MONTHS
    # -----------------------------------------

    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    # -----------------------------------------
    # ORDER RESULTS
    # -----------------------------------------

    payrolls = payrolls.order_by(
        "-year",
        "-generated_on",
        "teacher__first_name",
    )

    return render(
        request,
        "students/payroll_list.html",
        {
            "payrolls": payrolls,
            "calendar_years": calendar_years,
            "months": months,
            "selected_year": selected_year,
            "selected_month": selected_month,
        },
    )


@login_required
@admin_or_bursar
def print_payslip(request, id):

    # -----------------------------------------
    # GET PAYROLL
    # -----------------------------------------

    payroll = get_object_or_404(
        Payroll.objects.select_related(
            "teacher",
            "school",
        ),
        id=id,
    )

    # -----------------------------------------
    # CHECK SCHOOL ACCESS
    # -----------------------------------------

    if not request.user.is_superuser:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

        # Prevent accessing another school's payslip
        if payroll.school_id != school.id:

            messages.error(
                request,
                "You do not have permission to view this payslip."
            )

            return redirect("students:payroll_list")

    else:

        # Superuser can print any school's payslip
        school = payroll.school

    # -----------------------------------------
    # PDF BUFFER
    # -----------------------------------------

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

    # -----------------------------------------
    # SCHOOL HEADER
    # -----------------------------------------

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

    story.append(
        Spacer(
            1,
            0.2 * inch,
        )
    )

    # -----------------------------------------
    # TITLE
    # -----------------------------------------

    story.append(
        Paragraph(
            "<b>EMPLOYEE PAYSLIP</b>",
            styles["Heading1"],
        )
    )

    story.append(
        Spacer(
            1,
            0.15 * inch,
        )
    )

    # -----------------------------------------
    # EMPLOYEE DETAILS
    # -----------------------------------------

    teacher = payroll.teacher

    employee_table = Table(
        [
            [
                "Employee",
                str(teacher),
            ],

            [
                "Month",
                payroll.month,
            ],

            [
                "Year",
                payroll.year,
            ],

            [
                "Date Generated",
                payroll.generated_on,
            ],
        ],
        colWidths=[
            2.2 * inch,
            4.2 * inch,
        ],
    )

    employee_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(employee_table)

    story.append(
        Spacer(
            1,
            0.2 * inch,
        )
    )

    # -----------------------------------------
    # SALARY BREAKDOWN
    # -----------------------------------------

    salary_table = Table(
        [
            [
                "Description",
                "Amount (KSh)",
            ],

            [
                "Basic Salary",
                payroll.basic_salary,
            ],

            [
                "Gross Salary",
                payroll.gross_salary,
            ],

            [
                "PAYE",
                payroll.paye,
            ],

            [
                "SHA",
                payroll.sha,
            ],

            [
                "NSSF",
                payroll.nssf,
            ],

            [
                "Other Deductions",
                payroll.other_deductions,
            ],

            [
                "Total Deductions",
                payroll.deductions,
            ],

            [
                "NET SALARY",
                payroll.net_salary,
            ],
        ],
        colWidths=[
            4.5 * inch,
            2 * inch,
        ],
    )

    salary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.darkblue,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.lightgreen,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(salary_table)

    story.append(
        Spacer(
            1,
            0.4 * inch,
        )
    )

    # -----------------------------------------
    # SIGNATURES
    # -----------------------------------------

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
        colWidths=[
            3.3 * inch,
            3.3 * inch,
        ],
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(signature_table)

    # -----------------------------------------
    # BUILD PDF
    # -----------------------------------------

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

    salary = get_object_or_404(
        SalaryStructure.objects.select_related(
            "teacher",
            "teacher__school",
        ),
        id=id,
    )

    teacher = salary.teacher

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        school = teacher.school

    # -----------------------------------------
    # NORMAL SCHOOL USER
    # -----------------------------------------
    else:

        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user:

            messages.error(
                request,
                "Your account is not linked to a school."
            )

            return redirect("students:home")

        school = school_user.school

        # -------------------------------------
        # SECURITY CHECK
        # -------------------------------------

        if teacher.school_id != school.id:

            messages.error(
                request,
                "You cannot print a salary structure "
                "belonging to another school."
            )

            return redirect("students:salary_structure_list")

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

    # -----------------------------------------
    # SCHOOL HEADER
    # -----------------------------------------

    if school:

        story.append(
            Paragraph(
                f"<font size='18'><b>{school.name}</b></font>",
                styles["Title"],
            )
        )

        story.append(
            Paragraph(
                f"{school.address or ''}<br/>"
                f"Tel: {school.phone or ''}<br/>"
                f"Email: {school.email or ''}",
                styles["Normal"],
            )
        )

    story.append(
        Spacer(
            1,
            0.2 * inch
        )
    )

    story.append(
        Paragraph(
            "<b>SALARY STRUCTURE</b>",
            styles["Heading1"],
        )
    )

    story.append(
        Spacer(
            1,
            0.15 * inch
        )
    )

    # -----------------------------------------
    # TEACHER DETAILS
    # -----------------------------------------

    teacher_table = Table(
        [
            [
                "Teacher",
                str(teacher),
            ],

            [
                "Bank",
                salary.bank_name or "-",
            ],

            [
                "Account Number",
                salary.account_number or "-",
            ],
        ],
        colWidths=[
            2.2 * inch,
            4.2 * inch,
        ],
    )

    teacher_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(teacher_table)

    story.append(
        Spacer(
            1,
            0.2 * inch
        )
    )

    # -----------------------------------------
    # SALARY BREAKDOWN
    # -----------------------------------------

    salary_table = Table(
        [
            [
                "Description",
                "Amount (KSh)",
            ],

            [
                "Basic Salary",
                salary.basic_salary,
            ],

            [
                "House Allowance",
                salary.house_allowance,
            ],

            [
                "Transport Allowance",
                salary.transport_allowance,
            ],

            [
                "Medical Allowance",
                salary.medical_allowance,
            ],

            [
                "Other Allowance",
                salary.other_allowance,
            ],

            [
                "Gross Salary",
                salary.gross_salary(),
            ],

            [
                "PAYE",
                salary.paye,
            ],

            [
                "SHA",
                salary.sha,
            ],

            [
                "NSSF",
                salary.nssf,
            ],

            [
                "Other Deductions",
                salary.other_deductions,
            ],

            [
                "Total Deductions",
                salary.total_deductions(),
            ],

            [
                "NET SALARY",
                salary.net_salary(),
            ],
        ],
        colWidths=[
            4.5 * inch,
            2 * inch,
        ],
    )

    salary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.darkblue,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.lightgreen,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
            ]
        )
    )

    story.append(salary_table)

    story.append(
        Spacer(
            1,
            0.35 * inch
        )
    )

    # -----------------------------------------
    # SIGNATURE SECTION
    # -----------------------------------------

    principal_name = (
        school.principal_name
        if school and school.principal_name
        else "Principal"
    )

    signature_table = Table(
        [
            [
                "______________________",
                "______________________",
            ],

            [
                "Teacher",
                principal_name,
            ],

            [
                "",
                "Principal",
            ],
        ],
        colWidths=[
            3.3 * inch,
            3.3 * inch,
        ],
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(signature_table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=(
            f"{teacher.first_name}_"
            f"{teacher.last_name}_"
            f"Salary_Structure.pdf"
        ),
    )