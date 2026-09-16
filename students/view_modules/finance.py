from datetime import datetime
from students.models import FeeLedgerEntry
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from reportlab.lib import colors
from datetime import date
from reportlab.lib.units import inch
from students.services.fee_ledger import (
    get_term_opening_balance,
    student_is_eligible_for_term,
    record_payment,
    record_term_fee_charges_for_class,
    get_term_carry_forward_credit,
    get_term_balance,
    
)

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
    StudentAcademicEnrollment,
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
def fee_structure_list(request):
    if request.user.is_superuser:
        fees = FeeStructure.objects.all()
    else:
        school = request.user.school_user.school

        fees = FeeStructure.objects.filter(
            school_class__school=school
        )

    return render(
        request,
        "students/fee_structure_list.html",
        {"fees": fees},
    )

@login_required
@admin_or_bursar
def edit_fee_structure(request, id):

    # -----------------------------------
    # Get fee structure
    # -----------------------------------

    try:
        fee_structure = (
            FeeStructure.objects
            .select_related(
                "school_class",
                "school_class__school",
            )
            .get(id=id)
        )
    except FeeStructure.DoesNotExist:
        messages.error(
            request,
            "Fee structure not found."
        )
        return redirect("students:fee_structure_list")

    # -----------------------------------
    # Determine school
    # -----------------------------------

    if request.user.is_superuser:

        school = fee_structure.school_class.school

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
            return redirect("students:finance_dashboard")

        school = school_user.school

        if (
            fee_structure.school_class.school_id
            != school.id
        ):
            messages.error(
                request,
                "You do not have permission to edit this fee structure."
            )
            return redirect("students:fee_structure_list")

    # -----------------------------------
    # Check whether ledger charges exist
    # -----------------------------------

    has_ledger_charges = (
        FeeLedgerEntry.objects
        .filter(
            school_id=school.id,
            transaction_type="FEE_CHARGE",
            academic_year=fee_structure.academic_year,
            term=fee_structure.term,
            reference__startswith="FEE-",
        )
        .exists()
    )

    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == "POST":

        academic_year = (
            request.POST.get("academic_year") or ""
        ).strip()

        enrollment_term = (
            request.POST.get("enrollment_term") or ""
        ).strip()

        school_class_id = (
            request.POST.get("school_class") or ""
        ).strip()

        if not academic_year:
            messages.error(
                request,
                "Academic year is required."
            )
            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )

        if enrollment_term not in {"1", "2", "3"}:
            messages.error(
                request,
                "Invalid term selected."
            )
            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )

        # -----------------------------------
        # Existing ledger charges
        # -----------------------------------

        if has_ledger_charges:

            # Once posted, period and class cannot move.
            academic_year = fee_structure.academic_year
            enrollment_term = fee_structure.term
            school_class_id = str(
                fee_structure.school_class_id
            )

        # -----------------------------------
        # Validate class
        # -----------------------------------

        try:
            school_class = SchoolClass.objects.get(
                id=school_class_id,
                school=school,
            )
        except SchoolClass.DoesNotExist:
            messages.error(
                request,
                "Please select a valid class."
            )
            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )

        # -----------------------------------
        # Prevent duplicate
        # -----------------------------------

        duplicate_exists = (
            FeeStructure.objects
            .filter(
                school_class=school_class,
                academic_year=academic_year,
                term=enrollment_term,
            )
            .exclude(id=fee_structure.id)
            .exists()
        )

        if duplicate_exists:
            messages.error(
                request,
                "A fee structure already exists for this "
                "class, academic year and term."
            )
            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )

        # -----------------------------------
        # Update
        # -----------------------------------

        fee_structure.school_class = school_class
        fee_structure.academic_year = academic_year
        fee_structure.term = enrollment_term

        # -----------------------------------
        # Validate fee amounts
        # -----------------------------------

        try:

            tuition_fee = Decimal(
                request.POST.get("tuition_fee") or "0"
            )

            activity_fee = Decimal(
                request.POST.get("activity_fee") or "0"
            )

            exam_fee = Decimal(
                request.POST.get("exam_fee") or "0"
            )

            other_fee = Decimal(
                request.POST.get("other_fee") or "0"
            )

        except (InvalidOperation, ValueError):

            messages.error(
                request,
                "Please enter valid fee amounts."
            )

            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )


        # -----------------------------------
        # Validate individual amounts
        # -----------------------------------

        if (
            tuition_fee < 0
            or activity_fee < 0
            or exam_fee < 0
            or other_fee < 0
        ):

            messages.error(
                request,
                "Fee amounts cannot be negative."
            )

            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )


        # -----------------------------------
        # Validate total
        # -----------------------------------

        total_fee = (
            tuition_fee
            + activity_fee
            + exam_fee
            + other_fee
        )

        if total_fee <= 0:

            messages.error(
                request,
                "The total fee must be greater than zero."
            )

            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )


        # -----------------------------------
        # Update fee structure
        # -----------------------------------

        fee_structure.tuition_fee = tuition_fee
        fee_structure.activity_fee = activity_fee
        fee_structure.exam_fee = exam_fee
        fee_structure.other_fee = other_fee

        fee_structure.save()
        fee_structure.save()

        # -----------------------------------
        # Synchronize ledger charges
        # -----------------------------------

        try:

            record_term_fee_charges_for_class(
                school_class=school_class,
                academic_year=academic_year,
                term=enrollment_term,
                recorded_by=request.user,
            )

        except Exception as exc:

            messages.error(
                request,
                f"Fee structure was saved but ledger "
                f"charges could not be synchronized: {exc}"
            )

            return redirect(
                "edit_fee_structure",
                id=fee_structure.id,
            )

        messages.success(
            request,
            "Fee structure updated successfully."
        )

        return redirect("students:fee_structure_list")

    # -----------------------------------
    # Academic years
    # -----------------------------------

    academic_years = (
        FeeStructure.objects
        .filter(
            school_class__school=school
        )
        .values_list(
            "academic_year",
            flat=True,
        )
        .distinct()
        .order_by("-academic_year")
    )

    # -----------------------------------
    # Classes
    # -----------------------------------

    classes = (
        SchoolClass.objects
        .filter(school=school)
        .order_by("name")
    )

    return render(
        request,
        "students/edit_fee_structure.html",
        {
            "fee_structure": fee_structure,
            "schools": SchoolProfile.objects.filter(
                id=school.id
            ),
            "classes": classes,
            "academic_years": academic_years,
            "academic_year": fee_structure.academic_year,
            "current_term": fee_structure.term,
            "enrollment_term": fee_structure.term,
            "has_ledger_charges": has_ledger_charges,
        },
    )


@login_required
@admin_or_bursar
def delete_fee_structure(request, id):

    # -----------------------------------
    # Get fee structure
    # -----------------------------------

    try:
        fee_structure = (
            FeeStructure.objects
            .select_related(
                "school_class",
                "school_class__school",
            )
            .get(id=id)
        )
    except FeeStructure.DoesNotExist:
        messages.error(
            request,
            "Fee structure not found."
        )
        return redirect("students:fee_structure_list")

    # -----------------------------------
    # Determine school
    # -----------------------------------

    if request.user.is_superuser:

        school = fee_structure.school_class.school

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
            return redirect("students:finance_dashboard")

        school = school_user.school

        if (
            fee_structure.school_class.school_id
            != school.id
        ):
            messages.error(
                request,
                "You do not have permission to delete this fee structure."
            )
            return redirect("students:fee_structure_list")

    # -----------------------------------
    # Check ledger
    # -----------------------------------

    has_ledger_charges = (
        FeeLedgerEntry.objects
        .filter(
            school_id=school.id,
            transaction_type="FEE_CHARGE",
            academic_year=fee_structure.academic_year,
            term=fee_structure.term,
            reference__startswith="FEE-",
        )
        .exists()
    )

    if has_ledger_charges:

        messages.error(
            request,
            "This fee structure has already been posted "
            "to the student ledger and cannot be deleted."
        )

        return redirect("students:fee_structure_list")

    # -----------------------------------
    # Confirm deletion
    # -----------------------------------

    if request.method == "POST":

        fee_structure.delete()

        messages.success(
            request,
            "Fee structure deleted successfully."
        )

        return redirect("students:fee_structure_list")

    return render(
        request,
        "students/delete_fee_structure.html",
        {
            "fee_structure": fee_structure,
        },
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






# ==========================
# FEE PAYMENTS
# ==========================
@login_required
@admin_or_bursar
@in_group("Administrators", "Bursar")
def fee_payment_list(request):

    # -------------------------------------------------
    # Determine the user's school
    # -------------------------------------------------
    if request.user.is_superuser:
        user_school = None
        schools = SchoolProfile.objects.all().order_by("name")
    else:
        school_user = getattr(request.user, "school_user", None)

        if not school_user or not school_user.school:
            return render(
                request,
                "students/fee_payment_list.html",
                {
                    "payments": FeePayment.objects.none(),
                    "schools": SchoolProfile.objects.none(),
                    "classes": SchoolClass.objects.none(),
                    "academic_years": [],
                    "terms": [],
                    "selected_school": "",
                    "selected_academic_year": "",
                    "selected_term": "",
                    "selected_class": "",
                },
            )

        user_school = school_user.school
        schools = SchoolProfile.objects.filter(
            pk=user_school.pk
        )

    # -------------------------------------------------
    # Selected filters
    # -------------------------------------------------
    selected_school = request.GET.get("school", "")
    selected_academic_year = request.GET.get("academic_year", "")
    selected_term = request.GET.get("term", "")
    selected_class = request.GET.get("school_class", "")

    # -------------------------------------------------
    # Determine active school filter
    # -------------------------------------------------
    if request.user.is_superuser:
        if selected_school:
            school_filter = SchoolProfile.objects.filter(
                pk=selected_school
            ).first()
        else:
            school_filter = None
    else:
        # NEVER allow a normal school user to switch schools
        school_filter = user_school

    # -------------------------------------------------
    # Base payment queryset
    # -------------------------------------------------
    payments = FeePayment.objects.select_related(
        "student",
        "student__school_class",
    )

    # -------------------------------------------------
    # School filter
    # -------------------------------------------------
    if school_filter:
        payments = payments.filter(
            student__school_class__school=school_filter
        )

    # -------------------------------------------------
    # Academic year / term filters
    #
    # These come from the student's FeeLedgerEntry
    # connected to this payment.
    # -------------------------------------------------
    if selected_academic_year:
        payments = payments.filter(
            ledger_entries__academic_year=selected_academic_year
        )

    if selected_term:
        payments = payments.filter(
            ledger_entries__term=selected_term
        )

    # -------------------------------------------------
    # Class filter
    # -------------------------------------------------
    if selected_class:
        payments = payments.filter(
            student__school_class_id=selected_class
        )

    # -------------------------------------------------
    # Remove duplicates and order
    # -------------------------------------------------
    payments = payments.distinct().order_by(
        "-payment_date",
        "-id",
    )

    # -------------------------------------------------
    # Academic years available for this school
    # -------------------------------------------------
    ledger_years = FeeLedgerEntry.objects.all()

    if school_filter:
        ledger_years = ledger_years.filter(
            school=school_filter
        )

    academic_years = (
        ledger_years
        .values_list("academic_year", flat=True)
        .distinct()
        .order_by("-academic_year")
    )

    # -------------------------------------------------
    # Classes available for this school
    # -------------------------------------------------
    if school_filter:
        classes = SchoolClass.objects.filter(
            school=school_filter
        ).order_by("name")
    else:
        classes = SchoolClass.objects.all().order_by(
            "school__name",
            "name",
        )

    # -------------------------------------------------
    # Terms
    # -------------------------------------------------
    terms = [
        "Term 1",
        "Term 2",
        "Term 3",
    ]

    return render(
        request,
        "students/fee_payment_list.html",
        {
            "payments": payments,
            "schools": schools,
            "classes": classes,
            "academic_years": academic_years,
            "terms": terms,

            "selected_school": selected_school,
            "selected_academic_year": selected_academic_year,
            "selected_term": selected_term,
            "selected_class": selected_class,
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
def fee_balance_list(request):


    # --------------------------------------------------
    # DETERMINE SCHOOL
    # --------------------------------------------------

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by("name")

        school_id = (
            request.GET.get("school") or ""
        ).strip()

        if school_id:

            try:
                school = SchoolProfile.objects.get(
                    id=school_id
                )
            except SchoolProfile.DoesNotExist:
                school = None

        else:
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

            return redirect("students:finance_dashboard")

        school = school_user.school

        schools = SchoolProfile.objects.filter(
            id=school.id
        )


    # --------------------------------------------------
    # FILTER VALUES
    # --------------------------------------------------

    academic_year = (
        request.GET.get("academic_year") or ""
    ).strip()

    enrollment_term = (
        request.GET.get("enrollment_term") or ""
    ).strip()

    selected_class = (
        request.GET.get("school_class") or ""
    ).strip()


    # Internal ledger term
    term = enrollment_term


        # --------------------------------------------------
    # ACADEMIC YEARS
    # --------------------------------------------------

    if school:

        # Start with academic years already present in
        # historical student enrollment records.
        existing_years = (
            StudentAcademicEnrollment.objects
            .filter(
                school_class__school=school
            )
            .values_list(
                "academic_year",
                flat=True,
            )
            .distinct()
        )

        academic_years = set(
            str(year).strip()
            for year in existing_years
            if str(year).strip()
        )

        # Also provide the same year range used by
        # Add Student:
        #
        # current year - 1
        # current year
        # current year + 1

        current_academic_year = (
            school.academic_year or ""
        ).strip()

        if current_academic_year:

            try:
                current_year = int(
                    current_academic_year
                )

                academic_years.add(
                    str(current_year - 1)
                )

                academic_years.add(
                    str(current_year)
                )

                academic_years.add(
                    str(current_year + 1)
                )

            except ValueError:

                academic_years.add(
                    current_academic_year
                )

        academic_years = sorted(
            academic_years,
            key=lambda value: (
                0,
                int(value)
            )
            if value.isdigit()
            else (
                1,
                value
            )
        )

        # Show newest year first.
        academic_years = list(
            reversed(academic_years)
        )

    else:

        # Superuser with no school selected:
        # combine all existing enrollment years
        # and configured school years.

        existing_years = (
            StudentAcademicEnrollment.objects
            .values_list(
                "academic_year",
                flat=True,
            )
            .distinct()
        )

        academic_years = set(
            str(year).strip()
            for year in existing_years
            if str(year).strip()
        )

        configured_years = (
            SchoolProfile.objects
            .exclude(
                academic_year=""
            )
            .values_list(
                "academic_year",
                flat=True,
            )
            .distinct()
        )

        for year in configured_years:

            try:
                year_int = int(
                    str(year).strip()
                )

                academic_years.add(
                    str(year_int - 1)
                )

                academic_years.add(
                    str(year_int)
                )

                academic_years.add(
                    str(year_int + 1)
                )

            except (TypeError, ValueError):

                cleaned_year = str(
                    year
                ).strip()

                if cleaned_year:
                    academic_years.add(
                        cleaned_year
                    )

        academic_years = sorted(
            academic_years,
            key=lambda value: (
                0,
                int(value)
            )
            if value.isdigit()
            else (
                1,
                value
            )
        )

        academic_years = list(
            reversed(academic_years)
        )

    # --------------------------------------------------
    # CLASSES
    # --------------------------------------------------

    if school:

        classes = (
            SchoolClass.objects
            .filter(school=school)
            .order_by("name")
        )

    else:

        classes = (
            SchoolClass.objects
            .all()
            .order_by("name")
        )


    # --------------------------------------------------
    # STUDENTS
    # --------------------------------------------------

    students = Student.objects.none()


    if (
        academic_year
        and enrollment_term in {"1", "2", "3"}
        and selected_class
    ):

        enrollment_query = (
            StudentAcademicEnrollment.objects
            .filter(
                academic_year=academic_year,
                term__lte=enrollment_term,
                school_class_id=selected_class,
            )
        )

        if school:

            enrollment_query = enrollment_query.filter(
                school_class__school=school
            )


        student_ids = (
            enrollment_query
            .values_list(
                "student_id",
                flat=True,
            )
            .distinct()
        )


        students = (
            Student.objects
            .select_related(
                "school",
                "school_class",
            )
            .filter(
                id__in=student_ids
            )
            .order_by(
                "admission_number"
            )
        )


    # --------------------------------------------------
    # BUILD REPORT
    # --------------------------------------------------

    student_rows = []


    if (
        academic_year
        and enrollment_term in {"1", "2", "3"}
        and selected_class
    ):

        for student in students:


            # ------------------------------------------
            # FIND HISTORICAL ENROLLMENT
            #
            # Use the latest enrollment at or before
            # the selected term.
            #
            # Example:
            #
            # T1 enrollment → student remains visible
            # in T2 until another enrollment is recorded.
            # ------------------------------------------

            enrollment = (
                StudentAcademicEnrollment.objects
                .filter(
                    student=student,
                    academic_year=academic_year,
                    term__lte=enrollment_term,
                )
                .select_related(
                    "school_class"
                )
                .order_by(
                    "-term",
                    "-id",
                )
                .first()
            )


            # ------------------------------------------
            # STUDENT ELIGIBILITY
            # ------------------------------------------

            if not student_is_eligible_for_term(
                student=student,
                academic_year=academic_year,
                term=term,
            ):
                continue


            # ------------------------------------------
            # HISTORICAL CLASS
            # ------------------------------------------

            if enrollment:

                historical_class = (
                    enrollment.school_class
                )

            else:

                historical_class = (
                    student.school_class
                )


            # ------------------------------------------
            # CLASS FILTER
            # ------------------------------------------

            if not historical_class:
                continue

            if str(
                historical_class.id
            ) != selected_class:
                continue


            # ------------------------------------------
            # CARRY FORWARD
            #
            # T1 = 0
            # T2 = T1 closing balance
            # T3 = T2 closing balance
            # ------------------------------------------

            if term == "1":
                try:
                    previous_academic_year = str(
                        int(academic_year) - 1
                    )
                    carry_forward = get_term_balance(
                        student=student,
                        academic_year=previous_academic_year,
                        term="3",
                    )
                except (TypeError, ValueError):
                    carry_forward = 0

            elif term == "2":
                carry_forward = get_term_balance(
                    student=student,
                    academic_year=academic_year,
                    term="1",
                )

            else:
                carry_forward = get_term_balance(
                    student=student,
                    academic_year=academic_year,
                    term="2",
                )

            # ------------------------------------------
            # CARRY FORWARD DISPLAY
            # ------------------------------------------

            if carry_forward > 0:

                carry_type = "Outstanding"
                carry_amount = carry_forward

            elif carry_forward < 0:

                carry_type = "Credit"
                carry_amount = abs(
                    carry_forward
                )

            else:

                carry_type = ""
                carry_amount = 0


            # ------------------------------------------
            # TERM FEE
            # ------------------------------------------

            fee_structure = None


            if historical_class:

                fee_structure = (
                    FeeStructure.objects
                    .filter(
                        school_class=historical_class,
                        academic_year=academic_year,
                        term=term,
                    )
                    .first()
                )


            if fee_structure:

                term_fee = (
                    fee_structure.total_fee
                )

                has_fee_structure = True

            else:

                term_fee = 0
                has_fee_structure = False


            # ------------------------------------------
            # CURRENT TERM PAYMENTS
            # ------------------------------------------

            payment_total = (
                FeeLedgerEntry.objects
                .filter(
                    student=student,
                    academic_year=academic_year,
                    term=term,
                    transaction_type="PAYMENT",
                )
                .aggregate(
                    total=Sum("credit")
                )["total"]
                or 0
            )


            # ------------------------------------------
            # CURRENT TERM BALANCE
            #
            # Carry Forward
            # + Term Fee
            # - Current Term Paid
            # ------------------------------------------

            balance = (
                carry_forward
                + term_fee
                - payment_total
            )


            # ------------------------------------------
            # BALANCE DISPLAY
            # ------------------------------------------

            if balance > 0:

                balance_type = "Outstanding"
                balance_amount = balance
                payment_status = "Outstanding"

            elif balance < 0:

                balance_type = "Credit"
                balance_amount = abs(balance)
                payment_status = "Credit"

            else:

                balance_type = ""
                balance_amount = 0
                payment_status = "Paid"


            # ------------------------------------------
            # REPORT ROW
            # ------------------------------------------

            student_rows.append(
                {
                    "student": student,

                    "historical_class": (
                        historical_class
                    ),

                    "carry_type": carry_type,

                    "carry_amount": carry_amount,

                    "term_fee": term_fee,

                    "has_fee_structure": (
                        has_fee_structure
                    ),

                    "paid": payment_total,

                    "balance_type": (
                        balance_type
                    ),

                    "balance_amount": (
                        balance_amount
                    ),

                    "payment_status": (
                        payment_status
                    ),
                }
            )


    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    return render(
        request,
        "fees/fee_balance_list.html",
        {
            "schools": schools,

            "academic_years": academic_years,

            "academic_year": academic_year,

            "current_term": enrollment_term,

            "enrollment_term": enrollment_term,

            "term": term,

            "classes": classes,

            "selected_class": selected_class,

            "student_rows": student_rows,

            "selected_school": school,
        },
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

        return redirect("students:fee_payment_list")

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
        return redirect("students:fee_payment_list")

    return render(
        request,
        "students/delete_payment.html",
        {
            "payment": payment,
        },
    )



@login_required
@admin_or_bursar
def add_fee_structure(request):

    # -----------------------------------
    # Determine schools
    # -----------------------------------

    if request.user.is_superuser:

        schools = (
            SchoolProfile.objects
            .all()
            .order_by("name")
        )

    else:

        school = request.user.school_user.school

        schools = SchoolProfile.objects.filter(
            id=school.id
        )

    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == "POST":

        # -----------------------------------
        # Determine selected school
        # -----------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get("school")

            try:
                school = SchoolProfile.objects.get(
                    id=school_id
                )
            except SchoolProfile.DoesNotExist:
                messages.error(
                    request,
                    "Please select a valid school."
                )
                return redirect("add_fee_structure")

        else:

            school = request.user.school_user.school

        # -----------------------------------
        # Current academic period
        # -----------------------------------

        current_academic_year = (
            school.academic_year or ""
        ).strip()

        current_term = (
            school.current_term or ""
        ).strip()

        if not current_academic_year or not current_term:
            messages.error(
                request,
                "The school's current academic year and term "
                "must be configured before adding a fee structure."
            )
            return redirect("add_fee_structure")

        # -----------------------------------
        # Selected academic period
        # -----------------------------------

        academic_year = (
            request.POST.get("academic_year") or ""
        ).strip()

        enrollment_term = (
            request.POST.get("enrollment_term") or ""
        ).strip()

        if not academic_year:
            messages.error(
                request,
                "Academic year is required."
            )
            return redirect("add_fee_structure")

        if enrollment_term not in ["1", "2", "3"]:
            messages.error(
                request,
                "Invalid enrollment term selected."
            )
            return redirect("add_fee_structure")

        term = enrollment_term

        # -----------------------------------
        # Class
        # -----------------------------------

        school_class_id = request.POST.get(
            "school_class"
        )

        try:
            school_class = SchoolClass.objects.get(
                id=school_class_id,
                school=school,
            )
        except SchoolClass.DoesNotExist:
            messages.error(
                request,
                "Please select a valid class."
            )
            return redirect("add_fee_structure")

        # -----------------------------------
        # Prevent duplicate
        # -----------------------------------

        if FeeStructure.objects.filter(
            school_class=school_class,
            academic_year=academic_year,
            term=term,
        ).exists():

            messages.error(
                request,
                "A fee structure already exists for this "
                "class, academic year and term."
            )

            return redirect("add_fee_structure")

        # -----------------------------------
        # Create fee structure
        # -----------------------------------

        fee_structure = FeeStructure.objects.create(
            school_class=school_class,
            academic_year=academic_year,
            term=term,
            tuition_fee=request.POST.get(
                "tuition_fee"
            ),
            activity_fee=request.POST.get(
                "activity_fee"
            ) or 0,
            exam_fee=request.POST.get(
                "exam_fee"
            ) or 0,
            other_fee=request.POST.get(
                "other_fee"
            ) or 0,
        )

        # -----------------------------------
        # Create ledger charges
        # -----------------------------------

        try:

            record_term_fee_charges_for_class(
                school_class=school_class,
                academic_year=academic_year,
                term=term,
                recorded_by=request.user,
            )

        except Exception as exc:

            fee_structure.delete()

            messages.error(
                request,
                f"Fee structure could not be processed: {exc}"
            )

            return redirect("add_fee_structure")

        messages.success(
            request,
            "Fee structure added successfully."
        )

        return redirect("students:fee_structure_list")

    # -----------------------------------
    # GET school / current period
    # -----------------------------------

    if request.user.is_superuser:

        school = None
        current_academic_year = ""
        current_term = ""

    else:

        school = request.user.school_user.school

        current_academic_year = (
            school.academic_year or ""
        ).strip()

        current_term = (
            school.current_term or ""
        ).strip()


    # -----------------------------------
    # Academic year dropdown
    # -----------------------------------
    # Keep all existing historical years,
    # but also expose current year -1, current year,
    # and current year +1, just like Add Student.

    existing_years = set(
        FeeStructure.objects
        .filter(
            school_class__school=school
        )
        .values_list("academic_year", flat=True)
        .distinct()
    ) if school else set(
        FeeStructure.objects
        .values_list("academic_year", flat=True)
        .distinct()
    )

    academic_years = set()

    # Preserve existing historical/future fee-structure years
    for year in existing_years:
        try:
            academic_years.add(int(str(year).strip()))
        except (TypeError, ValueError):
            pass

    # Selected school: use its configured academic year
    if school and current_academic_year:
        try:
            current_year = int(str(current_academic_year).strip())

            academic_years.update({
                current_year - 1,
                current_year,
                current_year + 1,
            })
        except (TypeError, ValueError):
            pass

    # Superuser without a selected school:
    # collect configured years from all schools.
    elif request.user.is_superuser:
        configured_years = (
            SchoolProfile.objects
            .exclude(academic_year__isnull=True)
            .exclude(academic_year="")
            .values_list("academic_year", flat=True)
        )

        for year in configured_years:
            try:
                current_year = int(str(year).strip())

                academic_years.update({
                    current_year - 1,
                    current_year,
                    current_year + 1,
                })
            except (TypeError, ValueError):
                pass

    academic_years = sorted(academic_years, reverse=True)
    # -----------------------------------
    # Classes
    # -----------------------------------

    if school:

        classes = (
            SchoolClass.objects
            .filter(school=school)
            .order_by("name")
        )

    else:

        classes = (
            SchoolClass.objects
            .all()
            .order_by("school__name", "name")
        )

    return render(
        request,
        "students/add_fee_structure.html",
        {
            "schools": schools,
            "classes": classes,
            "academic_years": academic_years,
            "academic_year": current_academic_year,
            "current_term": current_term,
        },
    )


@login_required
@admin_or_bursar
def add_fee_payment(request):

    # -----------------------------------
    # Determine school
    # -----------------------------------

    if request.user.is_superuser:

        schools = (
            SchoolProfile.objects
            .all()
            .order_by("name")
        )

        school_id = (
            request.POST.get("school")
            or request.GET.get("school")
        )

        if school_id:

            try:
                school = SchoolProfile.objects.get(
                    id=school_id
                )
            except SchoolProfile.DoesNotExist:
                school = None

        else:
            school = None

    else:

        school = request.user.school_user.school

        schools = SchoolProfile.objects.filter(
            id=school.id
        )

    # -----------------------------------
    # Classes for selected school
    # -----------------------------------

    if school:

        classes = (
            SchoolClass.objects
            .filter(
                school=school
            )
            .order_by("name")
        )

    else:

        classes = SchoolClass.objects.none()

    # -----------------------------------
    # Selected class
    # -----------------------------------

    selected_class_id = (
        request.POST.get("school_class")
        or request.GET.get("school_class")
        or ""
    )

    selected_class = None

    if school and selected_class_id:

        try:

            selected_class = (
                SchoolClass.objects
                .get(
                    id=selected_class_id,
                    school=school,
                )
            )

        except SchoolClass.DoesNotExist:

            selected_class = None

    # -----------------------------------
    # Current academic period
    # -----------------------------------

    current_academic_year = ""
    current_term = ""

    if school:

        current_academic_year = (
            school.academic_year or ""
        ).strip()

        current_term = (
            school.current_term or ""
        ).strip()

    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == "POST":

        if not school:

            messages.error(
                request,
                "Please select a valid school."
            )

            return redirect("add_fee_payment")

        # -----------------------------------
        # Academic period
        # -----------------------------------

        if not current_academic_year or not current_term:

            messages.error(
                request,
                "The school's current academic year and term "
                "must be configured before recording payments."
            )

            return redirect("add_fee_payment")

        academic_year = (
            request.POST.get("academic_year") or ""
        ).strip()

        enrollment_term = (
            request.POST.get("enrollment_term") or ""
        ).strip()

        if not academic_year:

            messages.error(
                request,
                "Academic year is required."
            )

            return redirect("add_fee_payment")

        if enrollment_term not in ["1", "2", "3"]:

            messages.error(
                request,
                "Invalid enrollment term selected."
            )

            return redirect("add_fee_payment")

        term = enrollment_term

        # -----------------------------------
        # Class
        # -----------------------------------

        class_id = request.POST.get("school_class")

        if not class_id:

            messages.error(
                request,
                "Please select a class."
            )

            return redirect("add_fee_payment")

        try:

            school_class = (
                SchoolClass.objects
                .get(
                    id=class_id,
                    school=school,
                )
            )

        except SchoolClass.DoesNotExist:

            messages.error(
                request,
                "Please select a valid class."
            )

            return redirect("add_fee_payment")

        # -----------------------------------
        # Student
        # -----------------------------------

        student_id = request.POST.get("student")

        try:

            student = (
                Student.objects
                .select_related(
                    "school",
                    "school_class",
                )
                .get(
                    id=student_id,
                    school=school,
                    school_class=school_class,
                )
            )

        except Student.DoesNotExist:

            messages.error(
                request,
                "Please select a valid student from the selected class."
            )

            return redirect(
                f"/fees/payments/add/?school={school.id}"
                f"&school_class={school_class.id}"
            )

        # -----------------------------------
        # Payment date
        # -----------------------------------

        payment_date = request.POST.get(
            "payment_date"
        )

        if not payment_date:

            messages.error(
                request,
                "Payment date is required."
            )

            return redirect("add_fee_payment")

        # -----------------------------------
        # Amount
        # -----------------------------------

        amount = request.POST.get("amount")

        if not amount:

            messages.error(
                request,
                "Payment amount is required."
            )

            return redirect("add_fee_payment")

        # -----------------------------------
        # Create payment
        # -----------------------------------

        payment = None

        try:

            payment = FeePayment.objects.create(
                student=student,
                amount=amount,
                payment_date=payment_date,
                payment_method=request.POST.get(
                    "payment_method"
                ),
                receipt_number=(
                    "RCPT-"
                    + uuid.uuid4().hex[:8].upper()
                ),
                reference=request.POST.get(
                    "reference",
                    "",
                ),
                remarks=request.POST.get(
                    "remarks",
                    "",
                ),
                academic_year=academic_year,
                term=term,
                recorded_by=request.user,
            )

            # -----------------------------------
            # Ledger
            # -----------------------------------

            record_payment(
                student=student,
                payment=payment,
                academic_year=academic_year,
                term=term,
                recorded_by=request.user,
            )

        except Exception as exc:

            if payment:
                payment.delete()

            messages.error(
                request,
                f"Payment could not be recorded: {exc}"
            )

            return redirect("add_fee_payment")

        messages.success(
            request,
            f"Payment recorded successfully. "
            f"Receipt: {payment.receipt_number}"
        )

        return redirect(
            "fee_statement",
            id=student.id,
        )

    # -----------------------------------
    # Academic years
    # -----------------------------------

    if school:

        existing_years = set(
            FeeStructure.objects
            .filter(
                school_class__school=school
            )
            .values_list(
                "academic_year",
                flat=True
            )
            .distinct()
        )

        academic_years = set()

        for year in existing_years:

            try:

                academic_years.add(
                    int(str(year).strip())
                )

            except (TypeError, ValueError):
                pass

        if current_academic_year:

            try:

                current_year = int(
                    str(current_academic_year).strip()
                )

                academic_years.update({
                    current_year - 1,
                    current_year,
                    current_year + 1,
                })

            except (TypeError, ValueError):
                pass

        academic_years = sorted(
            academic_years,
            reverse=True
        )

        # -----------------------------------
        # Students
        #
        # Filter by selected class when one
        # has been selected.
        # -----------------------------------

        students = (
            Student.objects
            .filter(
                school=school
            )
            .select_related(
                "school_class"
            )
        )

        if selected_class:

            students = students.filter(
                school_class=selected_class
            )

        students = students.order_by(
            "first_name",
            "last_name",
        )

    else:

        existing_years = set(
            FeeStructure.objects
            .values_list(
                "academic_year",
                flat=True
            )
            .distinct()
        )

        academic_years = set()

        for year in existing_years:

            try:

                academic_years.add(
                    int(str(year).strip())
                )

            except (TypeError, ValueError):
                pass

        configured_years = (
            SchoolProfile.objects
            .exclude(
                academic_year__isnull=True
            )
            .exclude(
                academic_year=""
            )
            .values_list(
                "academic_year",
                flat=True
            )
        )

        for year in configured_years:

            try:

                current_year = int(
                    str(year).strip()
                )

                academic_years.update({
                    current_year - 1,
                    current_year,
                    current_year + 1,
                })

            except (TypeError, ValueError):
                pass

        academic_years = sorted(
            academic_years,
            reverse=True
        )

        students = Student.objects.none()

    # -----------------------------------
    # Render
    # -----------------------------------

    return render(
        request,
        "students/add_fee_payment.html",
        {
            "schools": schools,
            "classes": classes,
            "students": students,
            "academic_years": academic_years,

            "academic_year": current_academic_year,
            "current_term": current_term,

            "selected_school": school,
            "selected_class": selected_class,
            "selected_class_id": selected_class_id,

            "today": date.today(),
        },
    )



@login_required
@admin_or_bursar
@in_group("Administrators", "Head Teacher", "Bursar")
def finance_dashboard(request):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        school = None

        students = Student.objects.select_related(
            "school_class",
            "school",
        )

        payments = FeePayment.objects.all()

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

            return redirect("home")

        school = school_user.school

        # -------------------------------------
        # ONLY THIS SCHOOL'S STUDENTS
        # -------------------------------------

        students = Student.objects.select_related(
            "school_class",
            "school",
        ).filter(
            school=school
        )

        # -------------------------------------
        # ONLY THIS SCHOOL'S PAYMENTS
        # -------------------------------------

        payments = FeePayment.objects.filter(
            student__school=school
        )

    # -----------------------------------------
    # TOTAL EXPECTED FEES
    # -----------------------------------------

    total_expected = 0

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

    # -----------------------------------------
    # TOTAL COLLECTED
    # -----------------------------------------

    total_collected = (
        payments.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # -----------------------------------------
    # OUTSTANDING BALANCE
    # -----------------------------------------

    outstanding = (
        total_expected
        - total_collected
    )

    # -----------------------------------------
    # TODAY'S COLLECTION
    # -----------------------------------------

    today_collection = (
        payments.filter(
            payment_date=date.today()
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # -----------------------------------------
    # NUMBER OF PAYMENTS
    # -----------------------------------------

    total_payments = payments.count()

    # -----------------------------------------
    # CONTEXT
    # -----------------------------------------

    return render(
        request,
        "fees/finance_dashboard.html",
        {
            "school": school,
            "total_expected": total_expected,
            "total_collected": total_collected,
            "outstanding": outstanding,
            "today_collection": today_collection,
            "total_payments": total_payments,
        },
    )