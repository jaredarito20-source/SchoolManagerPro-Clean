from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from reportlab.lib import colors
from datetime import date
from reportlab.lib.units import inch

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

    salaries = SalaryStructure.objects.select_related(
        "teacher"
    ).all()

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

    teachers = Teacher.objects.all()

    if request.method == "POST":

        SalaryStructure.objects.create(
            teacher=Teacher.objects.get(id=request.POST["teacher"]),
            basic_salary=request.POST["basic_salary"],
            house_allowance=request.POST["house_allowance"],
            medical_allowance=request.POST["medical_allowance"],
            transport_allowance=request.POST["transport_allowance"],
            other_allowance=request.POST["other_allowance"],
            paye=request.POST["paye"],
            sha=request.POST["sha"],
            nssf=request.POST["nssf"],
            other_deductions=request.POST.get("other_deductions", 0),
            bank_name=request.POST.get("bank_name", ""),
            account_number=request.POST.get("account_number", ""),
        )
        return redirect("salary_structure_list")

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

        return redirect("salary_structure_list")

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

        return redirect(
            "salary_structure_list"
        )

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

    if request.method == "POST":

        month = request.POST["month"]
        year = int(request.POST["year"])

        salary_structures = SalaryStructure.objects.select_related(
            "teacher"
        )

        for salary in salary_structures:

            if Payroll.objects.filter(
                teacher=salary.teacher,
                month=month,
                year=year,
            ).exists():
                continue

            gross_salary = salary.gross_salary()

            deductions = (
                salary.paye
                + salary.sha
                + salary.nssf
                + salary.other_deductions
            )

            net_salary = gross_salary - deductions

            Payroll.objects.create(
                teacher=salary.teacher,
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

        return redirect("payroll_list")

    return render(
        request,
        "students/generate_payroll.html",
    )

@login_required
@admin_or_bursar
def payroll_list(request):

    payrolls = Payroll.objects.select_related(
        "teacher"
    ).order_by(
        "-year",
        "-generated_on",
        "teacher__first_name",
    )

    return render(
        request,
        "students/payroll_list.html",
        {
            "payrolls": payrolls,
        },
    )

@login_required
@admin_or_bursar
def print_payslip(request, id):

    payroll = get_object_or_404(Payroll, id=id)
    school = SchoolProfile.objects.first()

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

    # School Header
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

    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "<b>EMPLOYEE PAYSLIP</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    # Employee Details

    teacher = payroll.teacher

    employee_table = Table(
        [
            ["Employee", str(teacher)],
            ["Month", payroll.month],
            ["Year", payroll.year],
            ["Date Generated", payroll.generated_on],
        ],
        colWidths=[2.2 * inch, 4.2 * inch],
    )

    employee_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(employee_table)

    story.append(Spacer(1, 0.2 * inch))

    # Salary Breakdown

    salary_table = Table(
        [
            ["Description", "Amount (KSh)"],

            ["Basic Salary", payroll.basic_salary],
            ["Gross Salary", payroll.gross_salary],

            ["PAYE", payroll.paye],
            ["SHA", payroll.sha],
            ["NSSF", payroll.nssf],
            ["Other Deductions", payroll.other_deductions],

            ["Total Deductions", payroll.deductions],

            ["NET SALARY", payroll.net_salary],
        ],
        colWidths=[4.5 * inch, 2 * inch],
    )

    salary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0,0), (-1,-1), 1, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),

                ("BACKGROUND", (0,-1), (-1,-1), colors.lightgreen),

                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),

                ("ALIGN", (1,1), (-1,-1), "RIGHT"),
            ]
        )
    )

    story.append(salary_table)

    story.append(Spacer(1, 0.4 * inch))

    # Signature Section

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
        colWidths=[3.3 * inch, 3.3 * inch],
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

    salary = get_object_or_404(SalaryStructure, id=id)
    school = SchoolProfile.objects.first()

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

    # School Header
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

    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "<b>SALARY STRUCTURE</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    # Teacher Details

    teacher_table = Table(
        [
            ["Teacher", str(salary.teacher)],
            ["Bank", salary.bank_name or "-"],
            ["Account Number", salary.account_number or "-"],
        ],
        colWidths=[2.2 * inch, 4.2 * inch],
    )

    teacher_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(teacher_table)

    story.append(Spacer(1, 0.2 * inch))

    # Salary Breakdown

    salary_table = Table(
        [
            ["Description", "Amount (KSh)"],

            ["Basic Salary", salary.basic_salary],
            ["House Allowance", salary.house_allowance],
            ["Transport Allowance", salary.transport_allowance],
            ["Medical Allowance", salary.medical_allowance],
            ["Other Allowance", salary.other_allowance],

            ["Gross Salary", salary.gross_salary()],

            ["PAYE", salary.paye],
            ["SHA", salary.sha],
            ["NSSF", salary.nssf],
            ["Other Deductions", salary.other_deductions],

            ["Total Deductions", salary.total_deductions()],

            ["NET SALARY", salary.net_salary()],
        ],
        colWidths=[4.5 * inch, 2 * inch],
    )

    salary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgreen),

                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )

    story.append(salary_table)

    story.append(Spacer(1, 0.35 * inch))

    # Signature Section

    signature_table = Table(
        [
            [
                "______________________",
                "______________________",
            ],
            [
                "Teacher",
                school.principal_name if school else "Principal",
            ],
            [
                "",
                "Principal",
            ],
        ],
        colWidths=[3.3 * inch, 3.3 * inch],
    )

    signature_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(signature_table)

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=f"{salary.teacher}_Salary_Structure.pdf",
    )
