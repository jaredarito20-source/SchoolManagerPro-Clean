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
@admin_or_bursar
def vehicle_list(request):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        vehicles = Vehicle.objects.select_related(
            "school",
            "driver",
        ).order_by(
            "registration_number"
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

        vehicles = Vehicle.objects.select_related(
            "school",
            "driver",
        ).filter(
            school=school_user.school
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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        school = None

        drivers = Driver.objects.filter(
            active=True
        ).select_related(
            "school"
        ).order_by(
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

        drivers = Driver.objects.filter(
            school=school,
            active=True,
        ).order_by(
            "first_name",
            "last_name",
        )

    # -----------------------------------------
    # SAVE VEHICLE
    # -----------------------------------------
    if request.method == "POST":

        # -------------------------------------
        # SUPERUSER SELECTS SCHOOL
        # -------------------------------------
        if request.user.is_superuser:

            school_id = request.POST.get(
                "school"
            )

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect("add_vehicle")

            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        # -------------------------------------
        # DRIVER
        # -------------------------------------

        driver = None

        driver_id = request.POST.get(
            "driver"
        )

        if driver_id:

            if request.user.is_superuser:

                driver = get_object_or_404(
                    Driver,
                    id=driver_id,
                    school=school,
                    active=True,
                )

            else:

                driver = get_object_or_404(
                    Driver,
                    id=driver_id,
                    school=school,
                    active=True,
                )

        # -------------------------------------
        # CREATE VEHICLE
        # -------------------------------------

        Vehicle.objects.create(

            school=school,

            registration_number=request.POST.get(
                "registration_number"
            ),

            vehicle_name=request.POST.get(
                "vehicle_name"
            ),

            make=request.POST.get(
                "make"
            ),

            capacity=request.POST.get(
                "capacity"
            ),

            driver=driver,

            status=request.POST.get(
                "status"
            ),
        )

        messages.success(
            request,
            "Vehicle added successfully."
        )

        return redirect("students:vehicle_list")

    # -----------------------------------------
    # SCHOOLS FOR SUPERUSER
    # -----------------------------------------

    schools = []

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

    # -----------------------------------------
    # FORM
    # -----------------------------------------

    return render(
        request,
        "students/add_vehicle.html",
        {
            "drivers": drivers,
            "schools": schools,
        },
    )
@login_required
@admin_or_bursar
def edit_vehicle(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        vehicle = get_object_or_404(
            Vehicle,
            id=id,
        )

        drivers = Driver.objects.filter(
            active=True
        ).order_by(
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

        vehicle = get_object_or_404(
            Vehicle,
            id=id,
            school=school,
        )

        drivers = Driver.objects.filter(
            school=school,
            active=True,
        ).order_by(
            "first_name",
            "last_name",
        )

    # -----------------------------------------
    # UPDATE VEHICLE
    # -----------------------------------------
    if request.method == "POST":

        vehicle.registration_number = request.POST.get(
            "registration_number"
        )

        vehicle.vehicle_name = request.POST.get(
            "vehicle_name"
        )

        vehicle.make = request.POST.get(
            "make"
        )

        vehicle.capacity = request.POST.get(
            "capacity"
        )

        vehicle.status = request.POST.get(
            "status"
        )

        # -------------------------------------
        # DRIVER
        # -------------------------------------

        driver_id = request.POST.get(
            "driver"
        )

        if driver_id:

            vehicle.driver = get_object_or_404(
                Driver,
                id=driver_id,
                school=vehicle.school,
                active=True,
            )

        else:

            vehicle.driver = None

        vehicle.save()

        messages.success(
            request,
            "Vehicle updated successfully."
        )

        return redirect("students:vehicle_list")

    # -----------------------------------------
    # SCHOOLS FOR SUPERUSER
    # -----------------------------------------

    schools = []

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

    return render(
        request,
        "students/edit_vehicle.html",
        {
            "vehicle": vehicle,
            "drivers": drivers,
            "schools": schools,
        },
    )

@login_required
@admin_or_bursar
def delete_vehicle(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        vehicle = get_object_or_404(
            Vehicle,
            id=id,
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

        vehicle = get_object_or_404(
            Vehicle,
            id=id,
            school=school,
        )

    # -----------------------------------------
    # DELETE
    # -----------------------------------------
    if request.method == "POST":

        vehicle.delete()

        messages.success(
            request,
            "Vehicle deleted successfully."
        )

        return redirect("students:vehicle_list")

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

    # -----------------------------------------
    # GET VEHICLE WITH SCHOOL
    # -----------------------------------------

    if request.user.is_superuser:

        vehicle = get_object_or_404(
            Vehicle.objects.select_related(
                "school",
                "driver",
            ),
            id=id,
        )

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

        vehicle = get_object_or_404(
            Vehicle.objects.select_related(
                "school",
                "driver",
            ),
            id=id,
            school=school,
        )

    # -----------------------------------------
    # VEHICLE SCHOOL
    # -----------------------------------------

    school = vehicle.school

    # -----------------------------------------
    # PDF BUFFER
    # -----------------------------------------

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
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
                    f"Tel: {school.phone}",
                    styles["Normal"],
                )
            )

        if school.email:

            story.append(
                Paragraph(
                    f"Email: {school.email}",
                    styles["Normal"],
                )
            )

    story.append(
        Spacer(
            1,
            0.25 * inch
        )
    )

    # -----------------------------------------
    # TITLE
    # -----------------------------------------

    story.append(
        Paragraph(
            "<b>VEHICLE DETAILS</b>",
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
    # DRIVER
    # -----------------------------------------

    driver = "Not Assigned"

    if vehicle.driver:

        driver = (
            f"{vehicle.driver.first_name} "
            f"{vehicle.driver.last_name}"
        )

    # -----------------------------------------
    # VEHICLE DATA
    # -----------------------------------------

    data = [

        [
            "Registration Number",
            vehicle.registration_number,
        ],

        [
            "Vehicle Name",
            vehicle.vehicle_name,
        ],

        [
            "Make / Model",
            vehicle.make or "-",
        ],

        [
            "Capacity",
            str(vehicle.capacity),
        ],

        [
            "Assigned Driver",
            driver,
        ],

        [
            "Status",
            vehicle.status,
        ],

    ]

    table = Table(
        data,
        colWidths=[
            2.6 * inch,
            3.8 * inch,
        ],
    )

    table.setStyle(
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
                    HexColor("#d9edf7"),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),

                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(
            1,
            0.5 * inch
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
                "Transport Officer",
                (
                    school.principal_name
                    if school
                    else "Principal"
                ),
            ],

            [
                "",
                "Principal",
            ],
        ],
        colWidths=[
            3 * inch,
            3 * inch,
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

    # -----------------------------------------
    # BUILD PDF
    # -----------------------------------------

    doc.build(story)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename=(
            f"{vehicle.registration_number}.pdf"
        ),
    )

@login_required
@admin_or_bursar
def transport_route_list(request):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        routes = TransportRoute.objects.select_related(
            "school",
            "vehicle",
            "driver",
        ).all().order_by(
            "route_name"
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

        routes = TransportRoute.objects.select_related(
            "school",
            "vehicle",
            "driver",
        ).filter(
            school=school
        ).order_by(
            "route_name"
        )

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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        school = None

        vehicles = Vehicle.objects.select_related(
            "school"
        ).all().order_by(
            "registration_number"
        )

        drivers = Driver.objects.filter(
            active=True
        ).order_by(
            "first_name",
            "last_name",
        )

        schools = SchoolProfile.objects.all().order_by(
            "name"
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

        vehicles = Vehicle.objects.filter(
            school=school
        ).order_by(
            "registration_number"
        )

        drivers = Driver.objects.filter(
            school=school,
            active=True,
        ).order_by(
            "first_name",
            "last_name",
        )

        schools = []

    # -----------------------------------------
    # SAVE ROUTE
    # -----------------------------------------
    if request.method == "POST":

        # -------------------------------------
        # SUPERUSER SELECTS SCHOOL
        # -------------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get(
                "school"
            )

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect(
                    "add_transport_route"
                )

            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        # -------------------------------------
        # VEHICLE
        # -------------------------------------

        vehicle = None

        vehicle_id = request.POST.get(
            "vehicle"
        )

        if vehicle_id:

            vehicle = get_object_or_404(
                Vehicle,
                id=vehicle_id,
                school=school,
            )

        # -------------------------------------
        # DRIVER
        # -------------------------------------

        driver = None

        driver_id = request.POST.get(
            "driver"
        )

        if driver_id:

            driver = get_object_or_404(
                Driver,
                id=driver_id,
                school=school,
                active=True,
            )

        # -------------------------------------
        # CREATE ROUTE
        # -------------------------------------

        TransportRoute.objects.create(

            school=school,

            route_name=request.POST.get(
                "route_name"
            ),

            start_point=request.POST.get(
                "start_point"
            ),

            end_point=request.POST.get(
                "end_point"
            ),

            distance_km=request.POST.get(
                "distance_km"
            ),

            vehicle=vehicle,

            driver=driver,

            active="active" in request.POST,
        )

        messages.success(
            request,
            "Transport route added successfully."
        )

        return redirect("students:transport_route_list")

    # -----------------------------------------
    # RENDER
    # -----------------------------------------

    return render(
        request,
        "students/add_transport_route.html",
        {
            "vehicles": vehicles,
            "drivers": drivers,
            "schools": schools,
        },
    )
@login_required
@admin_or_bursar
def edit_transport_route(request, id):

    # -----------------------------------------
    # GET ROUTE
    # -----------------------------------------

    if request.user.is_superuser:

        route = get_object_or_404(
            TransportRoute,
            id=id,
        )

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

        vehicles = Vehicle.objects.all().order_by(
            "registration_number"
        )

        drivers = Driver.objects.filter(
            active=True
        ).order_by(
            "first_name",
            "last_name",
        )

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

        route = get_object_or_404(
            TransportRoute,
            id=id,
            school=school,
        )

        schools = []

        vehicles = Vehicle.objects.filter(
            school=school
        ).order_by(
            "registration_number"
        )

        drivers = Driver.objects.filter(
            school=school,
            active=True,
        ).order_by(
            "first_name",
            "last_name",
        )

    # -----------------------------------------
    # UPDATE ROUTE
    # -----------------------------------------

    if request.method == "POST":

        # -------------------------------------
        # SUPERUSER CAN CHANGE SCHOOL
        # -------------------------------------

        if request.user.is_superuser:

            school_id = request.POST.get(
                "school"
            )

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect(
                    "edit_transport_route",
                    id=id,
                )

            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        # -------------------------------------
        # ROUTE DETAILS
        # -------------------------------------

        route.route_name = request.POST.get(
            "route_name"
        )

        route.start_point = request.POST.get(
            "start_point"
        )

        route.end_point = request.POST.get(
            "end_point"
        )

        route.distance_km = request.POST.get(
            "distance_km"
        )

        # -------------------------------------
        # VEHICLE
        # -------------------------------------

        vehicle_id = request.POST.get(
            "vehicle"
        )

        if vehicle_id:

            route.vehicle = get_object_or_404(
                Vehicle,
                id=vehicle_id,
                school=school,
            )

        else:

            route.vehicle = None

        # -------------------------------------
        # DRIVER
        # -------------------------------------

        driver_id = request.POST.get(
            "driver"
        )

        if driver_id:

            route.driver = get_object_or_404(
                Driver,
                id=driver_id,
                school=school,
                active=True,
            )

        else:

            route.driver = None

        # -------------------------------------
        # SCHOOL
        # -------------------------------------

        route.school = school

        # -------------------------------------
        # STATUS
        # -------------------------------------

        route.active = (
            "active" in request.POST
        )

        route.save()

        messages.success(
            request,
            "Transport route updated successfully."
        )

        return redirect("students:transport_route_list")

    # -----------------------------------------
    # RENDER
    # -----------------------------------------

    return render(
        request,
        "students/edit_transport_route.html",
        {
            "route": route,
            "vehicles": vehicles,
            "drivers": drivers,
            "schools": schools,
        },
    )

@login_required
@admin_or_bursar
def delete_transport_route(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------

    if request.user.is_superuser:

        route = get_object_or_404(
            TransportRoute,
            id=id,
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

        route = get_object_or_404(
            TransportRoute,
            id=id,
            school=school,
        )

    # -----------------------------------------
    # DELETE
    # -----------------------------------------

    if request.method == "POST":

        route.delete()

        messages.success(
            request,
            "Transport route deleted successfully."
        )

        return redirect("students:transport_route_list")

    # -----------------------------------------
    # CONFIRMATION PAGE
    # -----------------------------------------

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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------

    if request.user.is_superuser:

        transports = StudentTransport.objects.select_related(
            "student",
            "student__school",
            "route",
            "route__school",
            "route__vehicle",
            "route__driver",
        ).all().order_by(
            "student__first_name",
            "student__last_name",
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

        transports = StudentTransport.objects.select_related(
            "student",
            "student__school",
            "route",
            "route__school",
            "route__vehicle",
            "route__driver",
        ).filter(
            student__school=school
        ).order_by(
            "student__first_name",
            "student__last_name",
        )

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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

        school_id = request.GET.get("school")

        school = None

        if school_id:
            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by("name") if school else SchoolClass.objects.none()

        class_id = request.GET.get("class")

        students = Student.objects.none()

        if class_id and school:

            students = Student.objects.filter(
                school=school,
                school_class_id=class_id,
            ).order_by(
                "first_name",
                "last_name",
            )

        routes = TransportRoute.objects.filter(
            school=school,
            active=True,
        ).select_related(
            "vehicle",
            "driver",
        ).order_by(
            "route_name"
        ) if school else TransportRoute.objects.none()

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

        schools = []

        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

        class_id = request.GET.get("class")

        students = Student.objects.none()

        if class_id:

            students = Student.objects.filter(
                school=school,
                school_class_id=class_id,
            ).order_by(
                "first_name",
                "last_name",
            )

        routes = TransportRoute.objects.filter(
            school=school,
            active=True,
        ).select_related(
            "vehicle",
            "driver",
        ).order_by(
            "route_name"
        )

    # -----------------------------------------
    # SAVE
    # -----------------------------------------

    if request.method == "POST":

        student_id = request.POST.get(
            "student"
        )

        route_id = request.POST.get(
            "route"
        )

        student = get_object_or_404(
            Student,
            id=student_id,
            school=school,
        )

        route = get_object_or_404(
            TransportRoute,
            id=route_id,
            school=school,
            active=True,
        )

        # -------------------------------------
        # PREVENT DUPLICATE ASSIGNMENT
        # -------------------------------------

        if StudentTransport.objects.filter(
            student=student
        ).exists():

            messages.error(
                request,
                "This student is already assigned to transport."
            )

            return redirect(
                "add_student_transport"
            )

        # -------------------------------------
        # CREATE ASSIGNMENT
        # -------------------------------------

        StudentTransport.objects.create(

            student=student,

            route=route,

            pickup_point=request.POST.get(
                "pickup_point"
            ),

            dropoff_point=request.POST.get(
                "dropoff_point"
            ),

            active="active" in request.POST,
        )

        messages.success(
            request,
            "Student transport assigned successfully."
        )

        return redirect(
            "students:student_transport_list"
        )

    # -----------------------------------------
    # RENDER
    # -----------------------------------------

    return render(
        request,
        "students/add_student_transport.html",
        {
            "schools": schools,
            "classes": classes,
            "students": students,
            "routes": routes,
            "selected_school": (
                school.id
                if school
                else None
            ),
            "selected_class": class_id,
        },
    )
@login_required
@admin_or_bursar
def edit_student_transport(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        transport = get_object_or_404(
            StudentTransport,
            id=id,
        )

        students = Student.objects.all().order_by(
            "first_name",
            "last_name",
        )

        routes = TransportRoute.objects.filter(
            active=True,
        ).order_by("route_name")

        classes = SchoolClass.objects.all().order_by(
            "name"
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

        # -------------------------------------
        # ONLY THIS SCHOOL'S TRANSPORT
        # -------------------------------------
        transport = get_object_or_404(
            StudentTransport.objects.select_related(
                "student",
                "route",
            ),
            id=id,
            student__school=school,
            route__school=school,
        )

        # -------------------------------------
        # ONLY THIS SCHOOL'S STUDENTS
        # -------------------------------------
        students = Student.objects.filter(
            school=school
        ).order_by(
            "first_name",
            "last_name",
        )

        # -------------------------------------
        # ONLY THIS SCHOOL'S ROUTES
        # -------------------------------------
        routes = TransportRoute.objects.filter(
            school=school,
            active=True,
        ).order_by(
            "route_name"
        )

        # -------------------------------------
        # ONLY THIS SCHOOL'S CLASSES
        # -------------------------------------
        classes = SchoolClass.objects.filter(
            school=school
        ).order_by(
            "name"
        )

    # -----------------------------------------
    # SAVE CHANGES
    # -----------------------------------------
    if request.method == "POST":

        student_id = request.POST.get("student")
        route_id = request.POST.get("route")

        if not student_id or not route_id:

            messages.error(
                request,
                "Please select a student and transport route."
            )

            return redirect(
                "edit_student_transport",
                id=id,
            )

        # -------------------------------------
        # GET VALID STUDENT
        # -------------------------------------
        student = get_object_or_404(
            students,
            id=student_id,
        )

        # -------------------------------------
        # GET VALID ROUTE
        # -------------------------------------
        route = get_object_or_404(
            routes,
            id=route_id,
        )

        # -------------------------------------
        # UPDATE TRANSPORT
        # -------------------------------------
        transport.student = student

        transport.route = route

        transport.pickup_point = request.POST.get(
            "pickup_point",
            ""
        )

        transport.dropoff_point = request.POST.get(
            "dropoff_point",
            ""
        )

        transport.active = (
            "active" in request.POST
        )

        transport.save()

        messages.success(
            request,
            "Student transport assignment updated successfully."
        )

        return redirect(
            "students:student_transport_list"
        )

    # -----------------------------------------
    # RENDER
    # -----------------------------------------
    return render(
        request,
        "students/edit_student_transport.html",
        {
            "transport": transport,
            "students": students,
            "routes": routes,
            "classes": classes,
        },
    )
@login_required
@admin_or_bursar
def delete_student_transport(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        transport = get_object_or_404(
            StudentTransport,
            id=id,
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

        transport = get_object_or_404(
            StudentTransport,
            id=id,
            student__school=school,
        )

    # -----------------------------------------
    # DELETE
    # -----------------------------------------
    if request.method == "POST":

        transport.delete()

        messages.success(
            request,
            "Student transport assignment deleted successfully."
        )

        return redirect(
            "students:student_transport_list"
        )

    # -----------------------------------------
    # CONFIRMATION PAGE
    # -----------------------------------------
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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        transport = get_object_or_404(
            StudentTransport.objects.select_related(
                "student",
                "route",
                "route__vehicle",
                "route__driver",
                "route__school",
            ),
            id=id,
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

        transport = get_object_or_404(
            StudentTransport.objects.select_related(
                "student",
                "route",
                "route__vehicle",
                "route__driver",
                "route__school",
            ),
            id=id,
            student__school=school,
        )

    # -----------------------------------------
    # PDF RESPONSE
    # -----------------------------------------
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Transport_'
        f'{transport.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    # -----------------------------------------
    # SCHOOL
    # -----------------------------------------
    school = transport.student.school

    if school:

        p.setFont(
            "Helvetica-Bold",
            18,
        )

        p.drawCentredString(
            300,
            800,
            school.name,
        )

        p.setFont(
            "Helvetica",
            10,
        )

        y = 780

        if school.address:
            p.drawCentredString(
                300,
                y,
                school.address,
            )
            y -= 15

        if school.phone:
            p.drawCentredString(
                300,
                y,
                f"Tel: {school.phone}",
            )
            y -= 15

        if school.email:
            p.drawCentredString(
                300,
                y,
                f"Email: {school.email}",
            )

    # -----------------------------------------
    # TITLE
    # -----------------------------------------
    p.setFont(
        "Helvetica-Bold",
        16,
    )

    p.drawCentredString(
        300,
        700,
        "STUDENT TRANSPORT DETAILS",
    )

    # -----------------------------------------
    # DETAILS
    # -----------------------------------------
    y = 660

    p.setFont(
        "Helvetica",
        12,
    )

    p.drawString(
        50,
        y,
        f"Student: "
        f"{transport.student.first_name} "
        f"{transport.student.last_name}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Admission No: "
        f"{transport.student.admission_number}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Route: "
        f"{transport.route.route_name}",
    )

    y -= 25

    # -----------------------------------------
    # VEHICLE
    # -----------------------------------------
    if transport.route.vehicle:

        p.drawString(
            50,
            y,
            f"Vehicle: "
            f"{transport.route.vehicle.registration_number}",
        )

    else:

        p.drawString(
            50,
            y,
            "Vehicle: None",
        )

    y -= 25

    # -----------------------------------------
    # DRIVER
    # -----------------------------------------
    if transport.route.driver:

        p.drawString(
            50,
            y,
            f"Driver: "
            f"{transport.route.driver.first_name} "
            f"{transport.route.driver.last_name}",
        )

    else:

        p.drawString(
            50,
            y,
            "Driver: None",
        )

    y -= 25

    p.drawString(
        50,
        y,
        f"Pickup Point: "
        f"{transport.pickup_point or '-'}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Dropoff Point: "
        f"{transport.dropoff_point or '-'}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Assigned Date: "
        f"{transport.assigned_date}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Status: "
        f"{'Active' if transport.active else 'Inactive'}",
    )

    # -----------------------------------------
    # FOOTER
    # -----------------------------------------
    y -= 50

    p.setFont(
        "Helvetica",
        9,
    )

    p.drawString(
        50,
        y,
        "Generated by School Management System",
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def print_transport_route(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        route = get_object_or_404(
            TransportRoute.objects.select_related(
                "school",
                "vehicle",
                "driver",
            ),
            id=id,
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

        route = get_object_or_404(
            TransportRoute.objects.select_related(
                "school",
                "vehicle",
                "driver",
            ),
            id=id,
            school=school,
        )

    # -----------------------------------------
    # PDF RESPONSE
    # -----------------------------------------
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Route_{route.route_name}.pdf"'
    )

    p = canvas.Canvas(response)

    # -----------------------------------------
    # SCHOOL HEADER
    # -----------------------------------------
    school = route.school

    if school:

        p.setFont(
            "Helvetica-Bold",
            18,
        )

        p.drawCentredString(
            300,
            800,
            school.name,
        )

        y = 780

        p.setFont(
            "Helvetica",
            10,
        )

        if school.address:
            p.drawCentredString(
                300,
                y,
                school.address,
            )
            y -= 15

        if school.phone:
            p.drawCentredString(
                300,
                y,
                f"Tel: {school.phone}",
            )
            y -= 15

        if school.email:
            p.drawCentredString(
                300,
                y,
                f"Email: {school.email}",
            )

    # -----------------------------------------
    # TITLE
    # -----------------------------------------
    p.setFont(
        "Helvetica-Bold",
        16,
    )

    p.drawCentredString(
        300,
        700,
        "TRANSPORT ROUTE DETAILS",
    )

    # -----------------------------------------
    # ROUTE DETAILS
    # -----------------------------------------
    y = 660

    p.setFont(
        "Helvetica",
        12,
    )

    p.drawString(
        50,
        y,
        f"Route: {route.route_name}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Start Point: {route.start_point}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"End Point: {route.end_point}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Distance: {route.distance_km} km",
    )

    y -= 25

    # -----------------------------------------
    # VEHICLE
    # -----------------------------------------
    if route.vehicle:

        p.drawString(
            50,
            y,
            f"Vehicle: "
            f"{route.vehicle.registration_number}",
        )

        y -= 25

        p.drawString(
            50,
            y,
            f"Vehicle Name: "
            f"{route.vehicle.vehicle_name}",
        )

    else:

        p.drawString(
            50,
            y,
            "Vehicle: None",
        )

    y -= 25

    # -----------------------------------------
    # DRIVER
    # -----------------------------------------
    if route.driver:

        p.drawString(
            50,
            y,
            f"Driver: "
            f"{route.driver.first_name} "
            f"{route.driver.last_name}",
        )

        y -= 25

        if route.driver.phone:

            p.drawString(
                50,
                y,
                f"Driver Phone: "
                f"{route.driver.phone}",
            )

    else:

        p.drawString(
            50,
            y,
            "Driver: None",
        )

    y -= 25

    # -----------------------------------------
    # STATUS
    # -----------------------------------------
    p.drawString(
        50,
        y,
        f"Status: "
        f"{'Active' if route.active else 'Inactive'}",
    )

    # -----------------------------------------
    # FOOTER
    # -----------------------------------------
    y -= 50

    p.setFont(
        "Helvetica",
        9,
    )

    p.drawString(
        50,
        y,
        "Generated by School Management System",
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def driver_list(request):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        drivers = Driver.objects.select_related(
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

        drivers = Driver.objects.select_related(
            "school"
        ).filter(
            school=school
        ).order_by(
            "first_name",
            "last_name",
        )

    return render(
        request,
        "students/driver_list.html",
        {
            "drivers": drivers,
        },
    )

@login_required
@admin_or_bursar
def add_driver(request):

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
    # SAVE DRIVER
    # -----------------------------------------
    if request.method == "POST":

        # -------------------------------------
        # SUPERUSER CAN CHOOSE SCHOOL
        # -------------------------------------
        if request.user.is_superuser:

            school_id = request.POST.get("school")

            if not school_id:

                messages.error(
                    request,
                    "Please select a school."
                )

                return redirect("add_driver")

            school = get_object_or_404(
                SchoolProfile,
                id=school_id,
            )

        Driver.objects.create(

            school=school,

            first_name=request.POST.get(
                "first_name"
            ),

            last_name=request.POST.get(
                "last_name"
            ),

            phone=request.POST.get(
                "phone"
            ),

            national_id=request.POST.get(
                "national_id"
            ),

            license_number=request.POST.get(
                "license_number"
            ),

            license_expiry=request.POST.get(
                "license_expiry"
            ),

            active="active" in request.POST,

        )

        messages.success(
            request,
            "Driver added successfully."
        )

        return redirect("students:driver_list")

    # -----------------------------------------
    # SCHOOLS FOR SUPERUSER
    # -----------------------------------------
    schools = []

    if request.user.is_superuser:

        schools = SchoolProfile.objects.all().order_by(
            "name"
        )

    return render(
        request,
        "students/add_driver.html",
        {
            "schools": schools,
        },
    )
@login_required
@admin_or_bursar
def edit_driver(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        driver = get_object_or_404(
            Driver,
            id=id,
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

        driver = get_object_or_404(
            Driver,
            id=id,
            school=school,
        )

    # -----------------------------------------
    # UPDATE DRIVER
    # -----------------------------------------
    if request.method == "POST":

        driver.first_name = request.POST.get(
            "first_name"
        )

        driver.last_name = request.POST.get(
            "last_name"
        )

        driver.phone = request.POST.get(
            "phone"
        )

        driver.national_id = request.POST.get(
            "national_id"
        )

        driver.license_number = request.POST.get(
            "license_number"
        )

        driver.license_expiry = request.POST.get(
            "license_expiry"
        )

        driver.active = "active" in request.POST

        driver.save()

        messages.success(
            request,
            "Driver updated successfully."
        )

        return redirect("students:driver_list")

    # -----------------------------------------
    # DISPLAY FORM
    # -----------------------------------------
    return render(
        request,
        "students/edit_driver.html",
        {
            "driver": driver,
        },
    )


@login_required
@admin_or_bursar
def delete_driver(request, id):

    if request.user.is_superuser:

        driver = get_object_or_404(
            Driver,
            id=id,
        )

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

        driver = get_object_or_404(
            Driver,
            id=id,
            school=school_user.school,
        )

    if request.method == "POST":

        driver.delete()

        messages.success(
            request,
            "Driver deleted successfully."
        )

        return redirect("students:driver_list")

    return render(
        request,
        "students/delete_driver.html",
        {
            "driver": driver,
        },
    )

@login_required
@admin_or_bursar
def print_driver(request, id):

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        driver = get_object_or_404(
            Driver,
            id=id,
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

        driver = get_object_or_404(
            Driver,
            id=id,
            school=school_user.school,
        )

    # -----------------------------------------
    # CREATE PDF
    # -----------------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Driver_{driver.id}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont(
        "Helvetica-Bold",
        16
    )

    p.drawString(
        200,
        800,
        "Driver Details"
    )

    y = 760

    p.setFont(
        "Helvetica",
        12
    )

    # School
    if driver.school:
        p.drawString(
            50,
            y,
            f"School: {driver.school.name}"
        )
        y -= 25

    p.drawString(
        50,
        y,
        f"Name: {driver.first_name} {driver.last_name}"
    )
    y -= 25

    p.drawString(
        50,
        y,
        f"Phone: {driver.phone}"
    )
    y -= 25

    p.drawString(
        50,
        y,
        f"National ID: {driver.national_id}"
    )
    y -= 25

    p.drawString(
        50,
        y,
        f"License No: {driver.license_number}"
    )
    y -= 25

    p.drawString(
        50,
        y,
        f"License Expiry: {driver.license_expiry}"
    )
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

    # -----------------------------------------
    # SUPERUSER
    # -----------------------------------------
    if request.user.is_superuser:

        vehicles = Vehicle.objects.all()

        drivers = Driver.objects.all()

        routes = TransportRoute.objects.all()

        transports = StudentTransport.objects.all()

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

        vehicles = Vehicle.objects.filter(
            school=school
        )

        drivers = Driver.objects.filter(
            school=school
        )

        routes = TransportRoute.objects.filter(
            school=school
        )

        transports = StudentTransport.objects.filter(
            student__school=school
        )

    # -----------------------------------------
    # COUNTS
    # -----------------------------------------

    total_vehicles = vehicles.count()

    # Your vehicle form currently uses:
    # Active / Maintenance
    available_vehicles = vehicles.filter(
        status="Active"
    ).count()

    total_drivers = drivers.count()

    total_routes = routes.count()

    total_students = transports.count()

    # -----------------------------------------
    # RECENT ASSIGNMENTS
    # -----------------------------------------

    recent_assignments = transports.select_related(
        "student",
        "route",
        "route__vehicle",
        "route__driver",
    ).order_by(
        "-id"
    )[:10]

    # -----------------------------------------
    # CONTEXT
    # -----------------------------------------

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