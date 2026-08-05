from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.pdfgen import canvas

from students.models import (
    Student,
    SchoolClass,
    Teacher,
    MedicalVisit,
    Medication,
    Prescription,
)

from students.decorators import admin_or_bursar
from students.utils import draw_school_header, draw_school_footer


@login_required
@admin_or_bursar
def medical_dashboard(request):

    total_visits = MedicalVisit.objects.count()

    under_treatment = MedicalVisit.objects.filter(
        status="Under Treatment"
    ).count()

    recovered = MedicalVisit.objects.filter(
        status="Recovered"
    ).count()

    referred = MedicalVisit.objects.filter(
        status="Referred"
    ).count()

    total_medications = Medication.objects.count()

    class_summary = (
        SchoolClass.objects
        .annotate(
            total_cases=Count(
                "students__medical_visits"
            )
        )
        .order_by("-total_cases")
    )

    common_illnesses = (
        MedicalVisit.objects
        .values("complaint")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(
        request,
        "students/medical_dashboard.html",
        {
            "total_visits": total_visits,
            "under_treatment": under_treatment,
            "recovered": recovered,
            "referred": referred,
            "total_medications": total_medications,
            "class_summary": class_summary,
            "common_illnesses": common_illnesses,
        },
    )

@login_required
@admin_or_bursar
def print_medical_dashboard(request):

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="Medical_Dashboard.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "MEDICAL DASHBOARD REPORT",
    )

    total_visits = MedicalVisit.objects.count()

    under_treatment = MedicalVisit.objects.filter(
        status="Under Treatment"
    ).count()

    recovered = MedicalVisit.objects.filter(
        status="Recovered"
    ).count()

    referred = MedicalVisit.objects.filter(
        status="Referred"
    ).count()

    total_medications = Medication.objects.count()

    y = 720

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "Medical Summary")

    y -= 30

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Total Medical Visits : {total_visits}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Under Treatment : {under_treatment}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Recovered : {recovered}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Hospital Referrals : {referred}",
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Available Medications : {total_medications}",
    )

    y -= 40

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Most Common Illnesses",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 10)

    p.drawString(60, y, "Illness")
    p.drawString(400, y, "Cases")

    y -= 10

    p.line(50, y, 540, y)

    y -= 20

    p.setFont("Helvetica", 10)

    illnesses = (
        MedicalVisit.objects
        .values("complaint")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    if illnesses:

        for illness in illnesses:

            p.drawString(
                60,
                y,
                illness["complaint"],
            )

            p.drawString(
                420,
                y,
                str(illness["total"]),
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
                    "MEDICAL DASHBOARD REPORT",
                )

                y = 720

                p.setFont("Helvetica", 10)

    else:

        p.drawString(
            60,
            y,
            "No medical records available.",
        )

        y -= 20

    y -= 20

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Cases by Class",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 10)

    p.drawString(60, y, "Class")
    p.drawString(420, y, "Cases")

    y -= 10

    p.line(50, y, 540, y)

    y -= 20

    p.setFont("Helvetica", 10)

    classes = (
        SchoolClass.objects
        .annotate(
            total_cases=Count(
                "students__medical_visits"
            )
        )
        .order_by("-total_cases")
    )

    for school_class in classes:

        p.drawString(
            60,
            y,
            school_class.name,
        )

        p.drawString(
            420,
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
                "MEDICAL DASHBOARD REPORT",
            )

            y = 720

            p.setFont("Helvetica", 10)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def medical_visit_list(request):

    visits = (
        MedicalVisit.objects
        .select_related(
            "student",
            "attended_by",
        )
        .order_by("-visit_date")
    )

    return render(
        request,
        "students/medical_visit_list.html",
        {
            "visits": visits,
        },
    )

@login_required
@admin_or_bursar
def add_medical_visit(request):

    classes = SchoolClass.objects.all().order_by("name")

    teachers = Teacher.objects.order_by("first_name")

    students = Student.objects.none()

    selected_class = None

    if request.method == "POST":

        selected_class = request.POST.get("school_class")

        if selected_class:

            students = Student.objects.filter(
                school_class_id=selected_class
            ).order_by(
                "admission_number"
            )

        if "save_visit" in request.POST:

            student = Student.objects.get(
                id=request.POST["student"]
            )

            teacher = Teacher.objects.get(
                id=request.POST["attended_by"]
            )

            MedicalVisit.objects.create(

                student=student,

                attended_by=teacher,

                visit_date=request.POST["visit_date"],

                complaint=request.POST["complaint"],

                diagnosis=request.POST["diagnosis"],

                treatment=request.POST["treatment"],

                temperature=request.POST["temperature"] or None,

                status=request.POST["status"],

            )

            return redirect("medical_visit_list")

    return render(
        request,
        "students/add_medical_visit.html",
        {
            "classes": classes,
            "students": students,
            "teachers": teachers,
            "selected_class": selected_class,
        },
    )

@login_required
@admin_or_bursar
def edit_medical_visit(request, pk):

    visit = get_object_or_404(
        MedicalVisit,
        pk=pk,
    )

    students = Student.objects.all()

    teachers = Teacher.objects.all()

    if request.method == "POST":

        visit.student = Student.objects.get(
            id=request.POST["student"]
        )

        visit.attended_by = Teacher.objects.get(
            id=request.POST["attended_by"]
        )

        visit.visit_date = request.POST["visit_date"]

        visit.complaint = request.POST["complaint"]

        visit.diagnosis = request.POST["diagnosis"]

        visit.treatment = request.POST["treatment"]

        visit.temperature = (
            request.POST["temperature"] or None
        )

        visit.status = request.POST["status"]

        visit.save()

        return redirect(
            "medical_visit_list"
        )

    return render(
        request,
        "students/edit_medical_visit.html",
        {
            "visit": visit,
            "students": students,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def delete_medical_visit(request, pk):

    visit = get_object_or_404(
        MedicalVisit,
        pk=pk,
    )

    if request.method == "POST":

        visit.delete()

        return redirect(
            "medical_visit_list"
        )

    return render(
        request,
        "students/delete_medical_visit.html",
        {
            "visit": visit,
        },
    )

@login_required
@admin_or_bursar
def print_medical_visit(request, pk):

    visit = get_object_or_404(
        MedicalVisit,
        pk=pk,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Medical_Visit_{visit.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "MEDICAL VISIT REPORT",
    )

    y = 720

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Student Information")

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Admission No: {visit.student.admission_number}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Student Name: {visit.student.first_name} {visit.student.last_name}"
    )

    y -= 20

    if visit.student.school_class:

        p.drawString(
            60,
            y,
            f"Class: {visit.student.school_class.name}"
        )

        y -= 20

    p.drawString(
        60,
        y,
        f"Visit Date: {visit.visit_date}"
    )

    y -= 35

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Medical Details"
    )

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Complaint: {visit.complaint}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Diagnosis: {visit.diagnosis}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Treatment: {visit.treatment}"
    )

    y -= 20

    temperature = (
        f"{visit.temperature} °C"
        if visit.temperature
        else "Not Recorded"
    )

    p.drawString(
        60,
        y,
        f"Temperature: {temperature}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Status: {visit.status}"
    )

    y -= 20

    attended_by = (
        f"{visit.attended_by.first_name} {visit.attended_by.last_name}"
        if visit.attended_by
        else "Not Assigned"
    )

    p.drawString(
        60,
        y,
        f"Attended By: {attended_by}"
    )

    # Prescription Section

    y -= 40

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Prescribed Medication"
    )

    y -= 25

    p.setFont("Helvetica-Bold", 10)

    p.drawString(60, y, "Medication")
    p.drawString(260, y, "Dosage")
    p.drawString(420, y, "Duration")

    y -= 10

    p.line(50, y, 540, y)

    y -= 20

    p.setFont("Helvetica", 10)

    prescriptions = visit.prescriptions.select_related(
        "medication"
    )

    if prescriptions.exists():

        for prescription in prescriptions:

            p.drawString(
                60,
                y,
                prescription.medication.name,
            )

            p.drawString(
                260,
                y,
                prescription.dosage,
            )

            p.drawString(
                420,
                y,
                prescription.duration,
            )

            y -= 18

    else:

        p.drawString(
            60,
            y,
            "No medication prescribed."
        )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response


@login_required
@admin_or_bursar
def medication_list(request):

    medications = Medication.objects.all().order_by("name")

    return render(
        request,
        "students/medication_list.html",
        {
            "medications": medications,
        },
    )

@login_required
@admin_or_bursar
def add_medication(request):

    if request.method == "POST":

        Medication.objects.create(
            name=request.POST["name"],
            description=request.POST["description"],
            quantity=request.POST["quantity"],
            expiry_date=request.POST["expiry_date"] or None,
        )

        return redirect("medication_list")

    return render(
        request,
        "students/add_medication.html",
    )

@login_required
@admin_or_bursar
def edit_medication(request, pk):

    medication = get_object_or_404(
        Medication,
        pk=pk,
    )

    if request.method == "POST":

        medication.name = request.POST["name"]
        medication.description = request.POST["description"]
        medication.quantity = request.POST["quantity"]
        medication.expiry_date = request.POST["expiry_date"] or None

        medication.save()

        return redirect("medication_list")

    return render(
        request,
        "students/edit_medication.html",
        {
            "medication": medication,
        },
    )

@login_required
@admin_or_bursar
def delete_medication(request, pk):

    medication = get_object_or_404(
        Medication,
        pk=pk,
    )

    if request.method == "POST":

        medication.delete()

        return redirect("medication_list")

    return render(
        request,
        "students/delete_medication.html",
        {
            "medication": medication,
        },
    )

@login_required
@admin_or_bursar
def print_medication_list(request):

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="Medication_List.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "MEDICATION LIST",
    )

    y = 720

    p.setFont("Helvetica-Bold", 11)

    p.drawString(50, y, "No")
    p.drawString(90, y, "Medication")
    p.drawString(280, y, "Quantity")
    p.drawString(380, y, "Expiry Date")

    y -= 10

    p.line(50, y, 540, y)

    y -= 20

    p.setFont("Helvetica", 10)

    medications = Medication.objects.all().order_by("name")

    for i, medication in enumerate(medications, start=1):

        p.drawString(50, y, str(i))
        p.drawString(90, y, medication.name)
        p.drawString(280, y, str(medication.quantity))

        expiry = (
            medication.expiry_date.strftime("%d/%m/%Y")
            if medication.expiry_date
            else "-"
        )

        p.drawString(380, y, expiry)

        y -= 20

        if y < 80:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "MEDICATION LIST",
            )

            y = 720

            p.setFont("Helvetica", 10)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response



@login_required
@admin_or_bursar
def medical_reports(request):
    return render(
        request,
        "students/medical_reports.html",
    )

@login_required
@admin_or_bursar
def print_medical_reports(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if not from_date or not to_date:
        return redirect("medical_reports")

    visits = MedicalVisit.objects.filter(
        visit_date__range=[from_date, to_date]
    )

    total_visits = visits.count()

    under_treatment = visits.filter(
        status="Under Treatment"
    ).count()

    recovered = visits.filter(
        status="Recovered"
    ).count()

    referred = visits.filter(
        status="Referred"
    ).count()

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Medical_Report_{from_date}_to_{to_date}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "MEDICAL REPORT"
    )

    y = 720

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        50,
        y,
        f"Reporting Period: {from_date} to {to_date}"
    )

    y -= 35

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Total Visits: {total_visits}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Under Treatment: {under_treatment}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Recovered: {recovered}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Hospital Referrals: {referred}"
    )

    y -= 40

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Medical Visit Details"
    )

    y -= 25

    p.setFont("Helvetica-Bold", 9)

    p.drawString(40, y, "Date")
    p.drawString(95, y, "Adm")
    p.drawString(145, y, "Student")
    p.drawString(290, y, "Complaint")
    p.drawString(430, y, "Status")

    y -= 10

    p.line(35, y, 560, y)

    y -= 18

    p.setFont("Helvetica", 8)

    for visit in visits.select_related("student"):

        if y < 80:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "MEDICAL REPORT"
            )

            y = 720

            p.setFont("Helvetica", 8)

        p.drawString(
            40,
            y,
            str(visit.visit_date)
        )

        p.drawString(
            95,
            y,
            visit.student.admission_number
        )

        p.drawString(
            145,
            y,
            f"{visit.student.first_name} {visit.student.last_name}"
        )

        p.drawString(
            290,
            y,
            visit.complaint[:22]
        )

        p.drawString(
            430,
            y,
            visit.status
        )

        y -= 18

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def prescription_list(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            "medical_visit__student__school_class",
            "medication",
        )
        .order_by("-medical_visit__visit_date", "-id")
    )

    classes = SchoolClass.objects.all()
    medications = Medication.objects.all()

    student_search = request.GET.get("student")
    class_id = request.GET.get("class")
    medication_id = request.GET.get("medication")

    if student_search:
        prescriptions = prescriptions.filter(
            medical_visit__student__first_name__icontains=student_search
        ) | prescriptions.filter(
            medical_visit__student__last_name__icontains=student_search
        ) | prescriptions.filter(
            medical_visit__student__admission_number__icontains=student_search
        )

    if class_id:
        prescriptions = prescriptions.filter(
            medical_visit__student__school_class_id=class_id
        )

    if medication_id:
        prescriptions = prescriptions.filter(
            medication_id=medication_id
        )

    total_prescriptions = prescriptions.count()

    total_quantity = sum(
        p.quantity for p in prescriptions
    )

    return render(
        request,
        "students/prescription_list.html",
        {
            "prescriptions": prescriptions,
            "classes": classes,
            "medications": medications,
            "total_prescriptions": total_prescriptions,
            "total_quantity": total_quantity,
        },
    )
@login_required
@admin_or_bursar
def add_prescription(request):

    classes = SchoolClass.objects.all()
    teachers = Teacher.objects.all()
    medications = Medication.objects.all()

    selected_class = request.POST.get("school_class") or request.GET.get("school_class")

    students = Student.objects.none()
    visits = MedicalVisit.objects.none()

    if selected_class:

        students = Student.objects.filter(
            school_class_id=selected_class
        ).order_by("first_name")

        visits = (
            MedicalVisit.objects.filter(
                student__school_class_id=selected_class
            )
            .select_related("student")
            .order_by("-visit_date", "-id")
        )
    if request.method == "POST" and "save_prescription" in request.POST:

        visit = MedicalVisit.objects.get(
            id=request.POST["medical_visit"]
        )

        visit_id = request.POST.get("medical_visit")

        if not visit_id:
            messages.error(request, "Please select a medical visit.")
            return redirect("add_prescription")

        visit = get_object_or_404(
            MedicalVisit,
            id=visit_id,
        )

        medication = get_object_or_404(
            Medication,
            id=request.POST["medication"],
        )

        quantity = int(request.POST["quantity"])

        Prescription.objects.create(
            medical_visit=visit,
            medication=medication,
            dosage=request.POST["dosage"],
            frequency=request.POST["frequency"],
            duration=request.POST["duration"],
            quantity=quantity,
            instructions=request.POST["instructions"],
        )

        # Reduce stock
        medication.quantity -= quantity
        medication.save()

        messages.success(
            request,
            "Prescription saved successfully."
        )

        return redirect("prescription_list")

    return render(
        request,
        "students/add_prescription.html",
        {
            "classes": classes,
            "students": students,
            "visits": visits,
            "medications": medications,
            "selected_class": selected_class,
        },
    )

@login_required
@admin_or_bursar
def edit_prescription(request, pk):

    prescription = get_object_or_404(
        Prescription,
        pk=pk,
    )

    classes = SchoolClass.objects.all()

    medications = Medication.objects.all()

    selected_class = (
        request.POST.get("school_class")
        or request.GET.get("school_class")
        or str(
            prescription.medical_visit.student.school_class.id
        )
    )

    visits = MedicalVisit.objects.filter(
        student__school_class_id=selected_class
    ).select_related(
        "student"
    ).order_by("-visit_date")

    if request.method == "POST":

        prescription.medical_visit = MedicalVisit.objects.get(
            id=request.POST["medical_visit"]
        )

        prescription.medication = Medication.objects.get(
            id=request.POST["medication"]
        )

        prescription.dosage = request.POST["dosage"]

        prescription.frequency = request.POST["frequency"]

        prescription.duration = request.POST["duration"]

        prescription.quantity = request.POST["quantity"]

        prescription.instructions = request.POST["instructions"]

        prescription.save()

        messages.success(
            request,
            "Prescription updated successfully."
        )

        return redirect(
            "prescription_list"
        )

    return render(
        request,
        "students/edit_prescription.html",
        {
            "prescription": prescription,
            "classes": classes,
            "medications": medications,
            "visits": visits,
            "selected_class": selected_class,
        },
    )

@login_required
@admin_or_bursar
def delete_prescription(request, pk):

    prescription = get_object_or_404(
        Prescription,
        pk=pk,
    )

    if request.method == "POST":

        # Restore medication stock
        medication = prescription.medication
        medication.quantity_in_stock += prescription.quantity
        medication.save()

        prescription.delete()

        messages.success(
            request,
            "Prescription deleted successfully."
        )

        return redirect(
            "prescription_list"
        )

    return render(
        request,
        "students/delete_prescription.html",
        {
            "prescription": prescription,
        },
    )

@login_required
@admin_or_bursar
def print_prescription(request, pk):

    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "medical_visit",
            "medical_visit__student",
            "medical_visit__reported_by",
            "medication",
        ),
        pk=pk,
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="Prescription_{prescription.id}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "MEDICAL PRESCRIPTION"
    )

    student = prescription.medical_visit.student

    visit = prescription.medical_visit

    y = 720

    p.setFont("Helvetica-Bold", 12)

    p.drawString(50, y, "Student Information")

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Admission No: {student.admission_number}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Student Name: {student.first_name} {student.last_name}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Class: {student.school_class.name}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Visit Date: {visit.visit_date}"
    )

    y -= 35

    p.setFont("Helvetica-Bold", 12)

    p.drawString(50, y, "Diagnosis")

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        visit.complaint
    )

    y -= 40

    p.setFont("Helvetica-Bold", 12)

    p.drawString(50, y, "Prescription")

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        60,
        y,
        f"Medication : {prescription.medication.name}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Dosage : {prescription.dosage}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Frequency : {prescription.frequency}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Duration : {prescription.duration}"
    )

    y -= 20

    p.drawString(
        60,
        y,
        f"Quantity : {prescription.quantity}"
    )

    y -= 30

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        "Instructions"
    )

    y -= 25

    p.setFont("Helvetica", 11)

    text = p.beginText(60, y)

    for line in prescription.instructions.splitlines():
        text.textLine(line)

    p.drawText(text)

    y = text.getY() - 50

    p.line(60, y, 220, y)
    p.drawString(90, y - 15, "Medical Officer")

    p.line(320, y, 500, y)
    p.drawString(365, y - 15, "Parent/Guardian")

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def view_prescription(request, pk):

    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "medical_visit__student__school_class",
            "medical_visit__reported_by",
            "medication",
        ),
        pk=pk,
    )

    return render(
        request,
        "students/view_prescription.html",
        {
            "prescription": prescription,
        },
    )



@login_required
@admin_or_bursar
def print_prescription_register(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            "medical_visit__student__school_class",
            "medication",
        )
        .order_by("-medical_visit__visit_date")
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="Prescription_Register.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b><font size=18>Prescription Register</font></b>",
            styles["Title"],
        )
    )

    elements.append(
        Paragraph(
            f"Printed By: {request.user.username}",
            styles["Normal"],
        )
    )

    elements.append(
        Paragraph(
            f"Total Prescriptions: {prescriptions.count()}",
            styles["Normal"],
        )
    )

    elements.append(Spacer(1, 15))

    data = [[
        "No",
        "Date",
        "Adm No",
        "Student",
        "Class",
        "Medication",
        "Qty",
        "Dosage",
        "Frequency",
        "Duration",
    ]]

    total_quantity = 0

    for i, prescription in enumerate(
        prescriptions,
        start=1,
    ):

        total_quantity += prescription.quantity

        data.append([
            i,
            str(prescription.medical_visit.visit_date),
            prescription.medical_visit.student.admission_number,
            str(prescription.medical_visit.student),
            str(prescription.medical_visit.student.school_class),
            prescription.medication.name,
            prescription.quantity,
            prescription.dosage,
            prescription.frequency,
            prescription.duration,
        ])

    table = Table(data)

    table.setStyle(

        TableStyle([

            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),

            ("TEXTCOLOR", (0,0), (-1,0), colors.white),

            ("GRID", (0,0), (-1,-1), 1, colors.black),

            ("BACKGROUND", (0,1), (-1,-1), colors.beige),

            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

            ("ALIGN", (0,0), (-1,-1), "CENTER"),

            ("BOTTOMPADDING", (0,0), (-1,0), 10),

        ])

    )

    elements.append(table)

    elements.append(Spacer(1,20))

    elements.append(

        Paragraph(

            f"<b>Total Medication Issued: {total_quantity}</b>",

            styles["Heading2"],

        )

    )

    doc.build(elements)

    return response







