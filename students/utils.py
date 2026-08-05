from datetime import datetime
from reportlab.lib.colors import HexColor

def draw_school_header(pdf, title):

    # School Name
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(HexColor("#003366"))
    pdf.drawCentredString(
        300,
        810,
        "YOUR SCHOOL NAME"
    )

    pdf.setFont("Helvetica", 11)

    pdf.setFillColor(HexColor("#000000"))

    pdf.drawCentredString(
        300,
        792,
        "P.O Box 12345 - Nairobi"
    )

    pdf.drawCentredString(
        300,
        777,
        "Phone: +254 700 000000"
    )

    pdf.drawCentredString(
        300,
        762,
        "Email: info@yourschool.ac.ke"
    )

    pdf.line(
        40,
        748,
        560,
        748,
    )

    pdf.setFont("Helvetica-Bold", 15)

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

    pdf.setFont("Helvetica", 9)

    pdf.drawString(
        40,
        25,
        f"Printed By: {request.user.username}"
    )

    pdf.drawRightString(
        560,
        25,
        datetime.now().strftime(
            "%d-%m-%Y %H:%M"
        )
    )
