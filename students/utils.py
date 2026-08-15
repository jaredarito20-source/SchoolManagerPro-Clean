from datetime import datetime
from reportlab.lib.colors import HexColor
from django.core.exceptions import PermissionDenied
from .models import Student


def get_user_school(user):

    if user.is_superuser:
        return None

    # School administrator / SchoolUser
    school_user = getattr(
        user,
        "school_user",
        None,
    )

    if school_user:
        return school_user.school

    # Teacher
    teacher = getattr(
        user,
        "teacher_profile",
        None,
    )

    if teacher and teacher.school:
        return teacher.school

    # Student
    student = getattr(
        user,
        "student_profile",
        None,
    )

    if student and student.school:
        return student.school

    # Parent
    child = (
        Student.objects
        .filter(
            parent_user=user,
            school__isnull=False,
        )
        .select_related("school")
        .first()
    )

    if child:
        return child.school

    raise PermissionDenied(
        "Your account is not connected to a school."
    )


def draw_school_header(pdf, title, school):

    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(
        HexColor("#003366")
    )

    pdf.drawCentredString(
        300,
        810,
        school.name,
    )

    pdf.setFont(
        "Helvetica",
        11,
    )

    pdf.setFillColor(
        HexColor("#000000")
    )

    if school.address:
        pdf.drawCentredString(
            300,
            792,
            school.address,
        )

    if school.phone:
        pdf.drawCentredString(
            300,
            777,
            f"Phone: {school.phone}",
        )

    if school.email:
        pdf.drawCentredString(
            300,
            762,
            f"Email: {school.email}",
        )

    pdf.line(
        40,
        748,
        560,
        748,
    )

    pdf.setFont(
        "Helvetica-Bold",
        15,
    )

    pdf.drawCentredString(
        300,
        728,
        title,
    )

    pdf.line(
        40,
        718,
        560,
        718,
    )


def draw_school_footer(pdf, request):

    pdf.line(
        40,
        40,
        560,
        40,
    )

    pdf.setFont(
        "Helvetica",
        9,
    )

    pdf.drawString(
        40,
        25,
        f"Printed By: {request.user.username}",
    )

    pdf.drawRightString(
        560,
        25,
        datetime.now().strftime(
            "%d-%m-%Y %H:%M"
        ),
    )