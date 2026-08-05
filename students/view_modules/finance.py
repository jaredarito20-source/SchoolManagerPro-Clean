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
@in_group("Administrators", "Bursar")
def print_receipt(request, id):

    payment = get_object_or_404(
        FeePayment,
        id=id
    )

    school = SchoolProfile.objects.first()

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

        if school.address:
            story.append(
                Paragraph(
                    school.address,
                    styles["Normal"],
                )
            )

        if school.phone:
            story.append(
                Paragraph(
                    f"Phone: {school.phone}",
                    styles["Normal"],
                )
            )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>OFFICIAL SCHOOL FEE RECEIPT</b>",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 15))

    data = [

        ["Receipt No", payment.receipt_number],

        [
            "Student",
            f"{payment.student.first_name} {payment.student.last_name}",
        ],

        [
            "Admission No",
            payment.student.admission_number,
        ],

        [
            "Class",
            payment.student.school_class.name,
        ],

        [
            "Amount Paid",
            f"KSh {payment.amount}",
        ],

        [
            "Payment Method",
            payment.payment_method,
        ],

        [
            "Reference",
            payment.reference,
        ],

        [
            "Payment Date",
            str(payment.payment_date),
        ],

        [
            "Recorded By",
            payment.recorded_by.username
            if payment.recorded_by
            else "",
        ],

    ]

    table = Table(
        data,
        colWidths=[170, 300],
    )

    table.setStyle(
        TableStyle([

            ("GRID", (0,0), (-1,-1), 1, colors.black),

            ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),

            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),

            ("BOTTOMPADDING", (0,0), (-1,-1), 8),

            ("TOPPADDING", (0,0), (-1,-1), 8),

        ])
    )

    story.append(table)

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            "Thank you for your payment.",
            styles["Heading3"],
        )
    )

    story.append(Spacer(1, 40))

    story.append(
        Paragraph(
            "__________________________",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "Bursar Signature",
            styles["Normal"],
        )
    )

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="Receipt.pdf",
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
@in_group("Administrators", "Bursar")
def fee_payment_list(request):

    payments = FeePayment.objects.select_related(
        "student",
        "student__school_class",
    ).order_by("-payment_date", "-id")

    return render(
        request,
        "students/fee_payment_list.html",
        {
            "payments": payments,
        },
    )





@login_required
@admin_or_bursar
@in_group("Administrators", "Head Teacher", "Bursar")
def print_fee_statement(request, id):

    student = Student.objects.get(id=id)

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("payment_date")

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    if fee_structure:
        total_fees = (
            fee_structure.tuition_fee
            + fee_structure.activity_fee
            + fee_structure.exam_fee
            + fee_structure.other_fee
        )
    else:
        total_fees = 0

    total_paid = payments.aggregate(
        total=Sum("amount")
    )["total"] or 0

    balance = total_fees - total_paid

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Fee Statement")

    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(170, y, "STUDENT FEE STATEMENT")

    y -= 40

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, y, f"Student: {student.first_name} {student.last_name}")
    y -= 20

    pdf.drawString(50, y, f"Admission No: {student.admission_number}")
    y -= 20

    pdf.drawString(50, y, f"Class: {student.school_class.name}")

    y -= 40

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(50, y, f"Total Fees : KSh {total_fees}")
    y -= 20

    pdf.drawString(50, y, f"Total Paid : KSh {total_paid}")
    y -= 20

    pdf.drawString(50, y, f"Balance    : KSh {balance}")

    y -= 40

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(50, y, "PAYMENT HISTORY")

    y -= 25

    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, y, "Date")
    pdf.drawString(140, y, "Receipt")
    pdf.drawString(280, y, "Method")
    pdf.drawString(430, y, "Amount")

    y -= 20

    for payment in payments:

        pdf.drawString(
            50,
            y,
            payment.payment_date.strftime("%d-%m-%Y"),
        )

        pdf.drawString(
            140,
            y,
            payment.receipt_number,
        )

        pdf.drawString(
            280,
            y,
            payment.payment_method,
        )

        pdf.drawString(
            430,
            y,
            f"KSh {payment.amount}",
        )

        y -= 20

        if y < 60:
            pdf.showPage()
            y = 800

    pdf.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="fee_statement.pdf",
    )

@login_required
@admin_or_bursar
@in_group(
    "Administrators",
    "Head Teacher",
    "Bursar",
)
def fee_statement(request, id):

    student = get_object_or_404(Student, id=id)

    payments = FeePayment.objects.filter(
        student=student
    ).order_by("-payment_date")

    # Get the student's fee structure
    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class
    ).first()

    if fee_structure:
        total_fees = (
            fee_structure.tuition_fee
            + fee_structure.activity_fee
            + fee_structure.exam_fee
            + fee_structure.other_fee
        )
    else:
        total_fees = 0

    total_paid = (
        payments.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    balance = total_fees - total_paid

    return render(
        request,
        "fees/fee_statement.html",
        {
            "student": student,
            "payments": payments,
            "total_fees": total_fees,
            "total_paid": total_paid,
            "balance": balance,
        },
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
@admin_or_bursar
def edit_payment(request, id):

    payment = FeePayment.objects.get(id=id)
    students = Student.objects.all()

    if request.method == "POST":

        payment.student = Student.objects.get(
            id=request.POST["student"]
        )

        payment.amount_paid = request.POST["amount_paid"]
        payment.payment_date = request.POST["payment_date"]
        payment.payment_method = request.POST["payment_method"]
        payment.receipt_number = request.POST["receipt_number"]

        payment.save()

        return redirect("fee_payment_list")

    return render(
        request,
        "students/edit_payment.html",
        {
            "payment": payment,
            "students": students,
        },
    )
@login_required
@admin_or_bursar
def delete_payment(request, id):

    payment = FeePayment.objects.get(id=id)

    if request.method == "POST":
        payment.delete()
        return redirect("fee_payment_list")

    return render(
        request,
        "students/delete_payment.html",
        {
            "payment": payment,
        },
    )

@login_required
@admin_or_bursar
@in_group("Administrators", "Bursar")
def add_fee_payment(request):

    students = Student.objects.select_related(
        "school_class"
    ).order_by(
        "admission_number"
    )

    if request.method == "POST":

        FeePayment.objects.create(

            student=Student.objects.get(
                id=request.POST["student"]
            ),

            amount=request.POST["amount"],

            payment_date=request.POST["payment_date"],

            payment_method=request.POST["payment_method"],

            receipt_number="RCPT-" + uuid.uuid4().hex[:8].upper(),

            reference=request.POST["reference"],

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Fee payment recorded successfully."
        )

        return redirect("fee_payment_list")

    return render(
    request,
    "students/add_fee_payment.html",
    {
        "students": students,
        "today": date.today(),
    },
)


@login_required
@admin_or_bursar
@in_group("Administrators", "Head Teacher", "Bursar")
def finance_dashboard(request):

    # Total expected fees
    total_expected = 0

    students = Student.objects.select_related("school_class")

    for student in students:

        structure = FeeStructure.objects.filter(
            school_class=student.school_class
        ).first()

        if structure:
            total_expected += (
                structure.tuition_fee
                + structure.activity_fee
                + structure.exam_fee
                + structure.other_fee
            )

    # Total collected
    total_collected = (
        FeePayment.objects.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # Outstanding balance
    outstanding = total_expected - total_collected

    # Today's collections
    today_collection = (
        FeePayment.objects.filter(
            payment_date=date.today()
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # Number of payments
    total_payments = FeePayment.objects.count()

    return render(
        request,
        "fees/finance_dashboard.html",
        {
            "total_expected": total_expected,
            "total_collected": total_collected,
            "outstanding": outstanding,
            "today_collection": today_collection,
            "total_payments": total_payments,
        },
    )


