from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.db.models import Count
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)


from reportlab.pdfgen import canvas

from students.models import *

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
    "Senior Teacher",
)
def vehicle_list(request):

    vehicles = Vehicle.objects.select_related(
        "driver"
    ).order_by(
        "registration_number"
    )

    return render(
        request,
        "students/vehicle_list.html",
        {
            "vehicles": vehicles,
        },
    )

@login_required
@admin_or_bursar
def add_vehicle(request):

    drivers = Driver.objects.filter(active=True)

    if request.method == "POST":

        driver = None

        if request.POST.get("driver"):
            driver = Driver.objects.get(id=request.POST["driver"])

        Vehicle.objects.create(
            registration_number=request.POST["registration_number"],
            vehicle_name=request.POST["vehicle_name"],
            make=request.POST["make"],
            capacity=request.POST["capacity"],
            driver=driver,
            status=request.POST["status"],
        )

        return redirect("vehicle_list")

    return render(
        request,
        "students/add_vehicle.html",
        {
            "drivers": drivers,
        },
    )

@login_required
@admin_or_bursar
def edit_vehicle(request, id):

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    drivers = Teacher.objects.all()

    if request.method == "POST":

        vehicle.registration_number = request.POST["registration_number"]
        vehicle.vehicle_name = request.POST["vehicle_name"]
        vehicle.make = request.POST["make"]
        vehicle.capacity = request.POST["capacity"]
        vehicle.status = request.POST["status"]

        if request.POST.get("driver"):
            vehicle.driver = Teacher.objects.get(
                id=request.POST["driver"]
            )
        else:
            vehicle.driver = None

        vehicle.save()

        return redirect("vehicle_list")

    return render(
        request,
        "students/edit_vehicle.html",
        {
            "vehicle": vehicle,
            "drivers": drivers,
        },
    )

@login_required
@admin_or_bursar
def delete_vehicle(request, id):

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    if request.method == "POST":
        vehicle.delete()
        return redirect("vehicle_list")

    return render(
        request,
        "students/delete_vehicle.html",
        {
            "vehicle": vehicle,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Senior Teacher",
)
def print_vehicle(request, id):

    school = SchoolProfile.objects.first()

    vehicle = get_object_or_404(
        Vehicle,
        id=id,
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
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
                school.address,
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Tel: {school.phone}",
                styles["Normal"],
            )
        )

        story.append(
            Paragraph(
                f"Email: {school.email}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 0.25 * inch))

    story.append(
        Paragraph(
            "<b>VEHICLE DETAILS</b>",
            styles["Heading1"],
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    driver = "-"

    if vehicle.driver:
        driver = (
            f"{vehicle.driver.first_name} "
            f"{vehicle.driver.last_name}"
        )

    data = [

        ["Registration Number", vehicle.registration_number],

        ["Vehicle Name", vehicle.vehicle_name],

        ["Make / Model", vehicle.make],

        ["Capacity", str(vehicle.capacity)],

        ["Assigned Driver", driver],

        ["Status", vehicle.status],

    ]

    table = Table(
        data,
        colWidths=[2.6 * inch, 3.8 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),

                ("BACKGROUND", (0, 0), (0, -1), HexColor("#d9edf7")),

                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 0.5 * inch))

    signature_table = Table(
        [
            [
                "_______________________",
                "_______________________",
            ],

            [
                "Transport Officer",
                school.principal_name if school else "Principal",
            ],

            [
                "",
                "Principal",
            ],
        ],
        colWidths=[3 * inch, 3 * inch],
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
        filename=f"{vehicle.registration_number}.pdf",
    )

@login_required
@admin_or_bursar
def transport_route_list(request):

    routes = TransportRoute.objects.select_related(
        "vehicle",
        "driver",
    ).all()

    return render(
        request,
        "students/transport_route_list.html",
        {
            "routes": routes,
        },
    )


@login_required
@admin_or_bursar
def add_transport_route(request):

    vehicles = Vehicle.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        TransportRoute.objects.create(
            route_name=request.POST["route_name"],
            start_point=request.POST["start_point"],
            end_point=request.POST["end_point"],
            distance_km=request.POST["distance_km"],
            vehicle=Vehicle.objects.get(id=request.POST["vehicle"])
            if request.POST["vehicle"] else None,
            driver=Teacher.objects.get(id=request.POST["driver"])
            if request.POST["driver"] else None,
            active="active" in request.POST,
        )

        return redirect("transport_route_list")

    return render(
        request,
        "students/add_transport_route.html",
        {
            "vehicles": vehicles,
            "teachers": teachers,
        },
    )

@login_required
@admin_or_bursar
def edit_transport_route(request, id):

    route = get_object_or_404(TransportRoute, id=id)

    vehicles = Vehicle.objects.all()
    teachers = Teacher.objects.all()

    if request.method == "POST":

        route.route_name = request.POST["route_name"]
        route.start_point = request.POST["start_point"]
        route.end_point = request.POST["end_point"]
        route.distance_km = request.POST["distance_km"]

        if request.POST["vehicle"]:
            route.vehicle = Vehicle.objects.get(
                id=request.POST["vehicle"]
            )
        else:
            route.vehicle = None

        if request.POST["driver"]:
            route.driver = Teacher.objects.get(
                id=request.POST["driver"]
            )
        else:
            route.driver = None

        route.active = "active" in request.POST

        route.save()

        return redirect("transport_route_list")

    return render(
        request,
        "students/edit_transport_route.html",
        {
            "route": route,
            "vehicles": vehicles,
            "teachers": teachers,
        },
    )


@login_required
@admin_or_bursar
def delete_transport_route(request, id):

    route = get_object_or_404(
        TransportRoute,
        id=id,
    )

    if request.method == "POST":

        route.delete()

        return redirect("transport_route_list")

    return render(
        request,
        "students/delete_transport_route.html",
        {
            "route": route,
        },
    )

@login_required
@admin_or_bursar
def student_transport_list(request):

    transports = StudentTransport.objects.select_related(
        "student",
        "route",
    ).all()

    return render(
        request,
        "students/student_transport_list.html",
        {
            "transports": transports,
        },
    )

@login_required
@admin_or_bursar
def add_student_transport(request):

    classes = SchoolClass.objects.all().order_by("name")

    class_id = request.GET.get("class")

    students = Student.objects.none()

    if class_id:
        students = Student.objects.filter(
            school_class_id=class_id
        ).order_by("first_name")

    routes = TransportRoute.objects.filter(active=True)

    if request.method == "POST":

        student = Student.objects.get(
            id=request.POST["student"]
        )

        route = TransportRoute.objects.get(
            id=request.POST["route"]
        )

        StudentTransport.objects.create(

            student=student,

            route=route,

            pickup_point=request.POST["pickup_point"],

            dropoff_point=request.POST["dropoff_point"],

            active="active" in request.POST,

        )

        return redirect("student_transport_list")

    return render(
        request,
        "students/add_student_transport.html",
        {
            "classes": classes,
            "students": students,
            "routes": routes,
            "selected_class": class_id,
        },
    )
@login_required
@admin_or_bursar
def edit_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    students = Student.objects.all()

    routes = TransportRoute.objects.filter(
        active=True,
    )

    if request.method == "POST":

        transport.student = Student.objects.get(
            id=request.POST["student"]
        )

        transport.route = TransportRoute.objects.get(
            id=request.POST["route"]
        )

        transport.pickup_point = request.POST["pickup_point"]

        transport.dropoff_point = request.POST["dropoff_point"]

        transport.active = "active" in request.POST

        transport.save()

        return redirect("student_transport_list")

    return render(
        request,
        "students/edit_student_transport.html",
        {
            "transport": transport,
            "students": students,
            "routes": routes,
        },
    )


@login_required
@admin_or_bursar
def delete_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    if request.method == "POST":

        transport.delete()

        return redirect("student_transport_list")

    return render(
        request,
        "students/delete_student_transport.html",
        {
            "transport": transport,
        },
    )

@login_required
@admin_or_bursar
def print_student_transport(request, id):

    transport = get_object_or_404(
        StudentTransport,
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Transport_{transport.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Student Transport Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Student: {transport.student.first_name} {transport.student.last_name}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Admission No: {transport.student.admission_number}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Route: {transport.route.route_name}"
    )

    y -= 25

    if transport.route.vehicle:

        p.drawString(
            50,
            y,
            f"Vehicle: {transport.route.vehicle.registration_number}"
        )

    else:

        p.drawString(
            50,
            y,
            "Vehicle: None"
        )

    y -= 25

    if transport.route.driver:

        p.drawString(
            50,
            y,
            f"Driver: {transport.route.driver.first_name} {transport.route.driver.last_name}"
        )

    else:

        p.drawString(
            50,
            y,
            "Driver: None"
        )

    y -= 25

    p.drawString(
        50,
        y,
        f"Pickup Point: {transport.pickup_point}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Dropoff Point: {transport.dropoff_point}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Assigned Date: {transport.assigned_date}"
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if transport.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

from reportlab.pdfgen import canvas

@login_required
@admin_or_bursar
def print_transport_route(request, id):

    route = get_object_or_404(TransportRoute, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Route_{route.route_name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Transport Route Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Route: {route.route_name}")
    y -= 25

    p.drawString(50, y, f"Start Point: {route.start_point}")
    y -= 25

    p.drawString(50, y, f"End Point: {route.end_point}")
    y -= 25

    if route.vehicle:
        p.drawString(
            50,
            y,
            f"Vehicle: {route.vehicle.registration_number}"
        )
    else:
        p.drawString(50, y, "Vehicle: None")

    y -= 25

    if route.driver:
        p.drawString(
            50,
            y,
            f"Driver: {route.driver.first_name} {route.driver.last_name}"
        )
    else:
        p.drawString(50, y, "Driver: None")

    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if route.active else 'Inactive'}"
    )

    p.save()

    return response

from reportlab.pdfgen import canvas


@login_required
@admin_or_bursar
def driver_list(request):

    drivers = Driver.objects.all().order_by("first_name")

    return render(
        request,
        "students/driver_list.html",
        {"drivers": drivers},
    )


@login_required
@admin_or_bursar
def add_driver(request):

    if request.method == "POST":

        Driver.objects.create(
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            phone=request.POST["phone"],
            national_id=request.POST["national_id"],
            license_number=request.POST["license_number"],
            license_expiry=request.POST["license_expiry"],
            active="active" in request.POST,
        )

        return redirect("driver_list")

    return render(request, "students/add_driver.html")


@login_required
@admin_or_bursar
def edit_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    if request.method == "POST":

        driver.first_name = request.POST["first_name"]
        driver.last_name = request.POST["last_name"]
        driver.phone = request.POST["phone"]
        driver.national_id = request.POST["national_id"]
        driver.license_number = request.POST["license_number"]
        driver.license_expiry = request.POST["license_expiry"]
        driver.active = "active" in request.POST

        driver.save()

        return redirect("driver_list")

    return render(
        request,
        "students/edit_driver.html",
        {"driver": driver},
    )


@login_required
@admin_or_bursar
def delete_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    if request.method == "POST":
        driver.delete()
        return redirect("driver_list")

    return render(
        request,
        "students/delete_driver.html",
        {"driver": driver},
    )


@login_required
@admin_or_bursar
def print_driver(request, id):

    driver = get_object_or_404(Driver, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Driver_{driver.id}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "Driver Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Name: {driver.first_name} {driver.last_name}")
    y -= 25

    p.drawString(50, y, f"Phone: {driver.phone}")
    y -= 25

    p.drawString(50, y, f"National ID: {driver.national_id}")
    y -= 25

    p.drawString(50, y, f"License No: {driver.license_number}")
    y -= 25

    p.drawString(50, y, f"License Expiry: {driver.license_expiry}")
    y -= 25

    p.drawString(
        50,
        y,
        f"Status: {'Active' if driver.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def transport_dashboard(request):

    total_vehicles = Vehicle.objects.count()

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).count()

    total_drivers = Driver.objects.count()

    total_routes = TransportRoute.objects.count()

    total_students = StudentTransport.objects.count()

    recent_assignments = StudentTransport.objects.select_related(
        "student",
        "route",
    ).order_by("-id")[:10]

    context = {

        "total_vehicles": total_vehicles,

        "available_vehicles": available_vehicles,

        "total_drivers": total_drivers,

        "total_routes": total_routes,

        "total_students": total_students,

        "recent_assignments": recent_assignments,

    }

    return render(
        request,
        "students/transport_dashboard.html",
        context,
    )



