from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse

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
def hostel_block_list(request):

    blocks = HostelBlock.objects.all()

    return render(
        request,
        "students/hostel_block_list.html",
        {"blocks": blocks},
    )


@login_required
@admin_or_bursar
def add_hostel_block(request):

    if request.method == "POST":

        HostelBlock.objects.create(

            name=request.POST["name"],

            description=request.POST["description"],

            active="active" in request.POST,

        )

        return redirect("hostel_block_list")

    return render(
        request,
        "students/add_hostel_block.html")


@login_required
@admin_or_bursar
def edit_hostel_block(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    if request.method == "POST":

        block.name = request.POST["name"]

        block.description = request.POST["description"]

        block.active = "active" in request.POST

        block.save()

        return redirect("hostel_block_list")

    return render(
        request,
        "students/edit_hostel_block.html",
        {"block": block},
    )


@login_required
@admin_or_bursar
def delete_hostel_block(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    if request.method == "POST":

        block.delete()

        return redirect("hostel_block_list")

    return render(
        request,
        "students/delete_hostel_block.html",
        {"block": block},
    )

from reportlab.pdfgen import canvas

@login_required
@admin_or_bursar
def print_hostel_block(request, id):

    block = get_object_or_404(HostelBlock, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Block_{block.name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Block Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Block Name: {block.name}")
    y -= 30

    p.drawString(50, y, f"Description: {block.description}")
    y -= 30

    p.drawString(
        50,
        y,
        f"Status: {'Active' if block.active else 'Inactive'}"
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_room_list(request):

    rooms = HostelRoom.objects.select_related("block")

    return render(
        request,
        "students/hostel_room_list.html",
        {
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_room(request):

    blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        block = HostelBlock.objects.get(
            id=request.POST["block"]
        )

        room = HostelRoom.objects.create(
            block=block,
            room_number=request.POST["room_number"],
            capacity=int(request.POST["capacity"]),
        )

        # Automatically create beds
        for number in range(1, room.capacity + 1):

            HostelBed.objects.create(
                room=room,
                bed_number=f"Bed {number}",
            )

        messages.success(
            request,
            f"Room {room.room_number} created with {room.capacity} beds."
        )

        return redirect("hostel_room_list")

    return render(
        request,
        "students/add_hostel_room.html",
        {
            "blocks": blocks,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_room(request, id):

    room = get_object_or_404(
        HostelRoom,
        id=id,
    )

    blocks = HostelBlock.objects.filter(
        active=True,
    )

    if request.method == "POST":

        room.block = HostelBlock.objects.get(
            id=request.POST["block"]
        )

        room.room_number = request.POST["room_number"]

        new_capacity = int(request.POST["capacity"])

        occupied_beds = HostelBed.objects.filter(
            room=room,
            occupied=True,
        ).count()

        if new_capacity < occupied_beds:

            messages.error(
                request,
                f"Capacity cannot be reduced below {occupied_beds} occupied beds."
            )

            return redirect(
                "edit_hostel_room",
                id=room.id,
            )

        old_capacity = room.capacity

        room.capacity = new_capacity

        room.save()

        # If capacity increased, create new beds
        if new_capacity > old_capacity:

            for number in range(old_capacity + 1, new_capacity + 1):

                HostelBed.objects.create(
                    room=room,
                    bed_number=f"Bed {number}",
                )

        # If capacity reduced, remove only unused highest-numbered beds
        elif new_capacity < old_capacity:

            beds_to_remove = HostelBed.objects.filter(
                room=room,
                occupied=False,
            ).order_by("-id")

            excess = old_capacity - new_capacity

            for bed in beds_to_remove[:excess]:
                bed.delete()

        messages.success(
            request,
            "Hostel room updated successfully."
        )

        return redirect(
            "hostel_room_list"
        )

    return render(
        request,
        "students/edit_hostel_room.html",
        {
            "room": room,
            "blocks": blocks,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_room(request, id):

    room = get_object_or_404(HostelRoom, id=id)

    if request.method == "POST":

        room.delete()

        return redirect("hostel_room_list")

    return render(
        request,
        "students/delete_hostel_room.html",
        {"room": room},
    )

@login_required
@admin_or_bursar
def print_hostel_room(request, id):

    room = get_object_or_404(HostelRoom, id=id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Room_{room.room_number}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Room Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Block: {room.block.name}")
    y -= 30

    p.drawString(50, y, f"Room: {room.room_number}")
    y -= 30

    p.drawString(50, y, f"Capacity: {room.capacity}")
    y -= 30

    p.drawString(50, y, f"Occupied: {room.occupied}")

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def student_hostel_list(request):

    allocations = StudentHostel.objects.select_related(
        "student",
        "room",
        "room__block"
    )

    return render(
        request,
        "students/student_hostel_list.html",
        {"allocations": allocations},
    )

@login_required
@admin_or_bursar
def add_student_hostel(request):

    students = Student.objects.filter(
        hostel__isnull=True
    )

    rooms = HostelRoom.objects.select_related(
        "block"
    )

    if request.method == "POST":

        student = Student.objects.get(
            id=request.POST["student"]
        )

        room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        bed = HostelBed.objects.get(
            id=request.POST["bed"]
        )

        if bed.occupied:

            messages.error(
                request,
                "This bed is already occupied."
            )

            return redirect(
                "add_student_hostel"
            )

        StudentHostel.objects.create(

            student=student,

            room=room,

            bed=bed,

        )

        bed.occupied = True
        bed.save()

        messages.success(
            request,
            "Student allocated successfully."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/add_student_hostel.html",
        {
            "students": students,
            "rooms": rooms,
        },
    )
@login_required
@admin_or_bursar
def edit_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
    )

    rooms = HostelRoom.objects.select_related(
        "block"
    )

    if request.method == "POST":

        new_room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        new_bed = HostelBed.objects.get(
            id=request.POST["bed"]
        )

        if new_bed.occupied and new_bed != allocation.bed:

            messages.error(
                request,
                "Selected bed is already occupied."
            )

            return redirect(
                "edit_student_hostel",
                id=id,
            )

        # Free old bed
        allocation.bed.occupied = False
        allocation.bed.save()

        # Occupy new bed
        new_bed.occupied = True
        new_bed.save()

        allocation.room = new_room
        allocation.bed = new_bed

        allocation.save()

        messages.success(
            request,
            "Allocation updated successfully."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/edit_student_hostel.html",
        {
            "allocation": allocation,
            "rooms": rooms,
        },
    )
@login_required
@admin_or_bursar
def delete_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
    )

    if request.method == "POST":

        allocation.bed.occupied = False
        allocation.bed.save()

        allocation.delete()

        messages.success(
            request,
            "Student removed from hostel."
        )

        return redirect(
            "student_hostel_list"
        )

    return render(
        request,
        "students/delete_student_hostel.html",
        {
            "allocation": allocation,
        },
    )
@login_required
@admin_or_bursar
def print_student_hostel(request, id):

    allocation = get_object_or_404(
        StudentHostel.objects.select_related(
            "student",
            "room",
            "room__block",
            "bed",
        ),
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Allocation_{allocation.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL ALLOCATION",
    )

    y = 690

    p.drawString(
        50,
        y,
        f"Admission Number : {allocation.student.admission_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Student : {allocation.student.first_name} {allocation.student.last_name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Class : {allocation.student.school_class}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Hostel Block : {allocation.room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room : {allocation.room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Bed : {allocation.bed.bed_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Assigned : {allocation.assigned_date}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_warden_list(request):

    wardens = HostelWarden.objects.select_related(
        "hostel_block"
    )

    return render(
        request,
        "students/hostel_warden_list.html",
        {
            "wardens": wardens,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_warden(request):

    hostel_blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        HostelWarden.objects.create(

            first_name=request.POST["first_name"],

            last_name=request.POST["last_name"],

            gender=request.POST["gender"],

            phone=request.POST["phone"],

            email=request.POST["email"],

            hostel_block=HostelBlock.objects.get(
                id=request.POST["hostel_block"]
            ),

            active="active" in request.POST,

        )

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/add_hostel_warden.html",
        {
            "hostel_blocks": hostel_blocks,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    hostel_blocks = HostelBlock.objects.filter(active=True)

    if request.method == "POST":

        warden.first_name = request.POST["first_name"]
        warden.last_name = request.POST["last_name"]
        warden.gender = request.POST["gender"]
        warden.phone = request.POST["phone"]
        warden.email = request.POST["email"]

        warden.hostel_block = HostelBlock.objects.get(
            id=request.POST["hostel_block"]
        )

        warden.active = "active" in request.POST

        warden.save()

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/edit_hostel_warden.html",
        {
            "warden": warden,
            "hostel_blocks": hostel_blocks,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    if request.method == "POST":

        warden.delete()

        return redirect("hostel_warden_list")

    return render(
        request,
        "students/delete_hostel_warden.html",
        {
            "warden": warden,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_warden(request, id):

    warden = get_object_or_404(
        HostelWarden,
        id=id,
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Warden_{warden.first_name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(170, 800, "Hostel Warden Details")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Name: {warden.first_name} {warden.last_name}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Gender: {warden.gender}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Phone: {warden.phone}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Email: {warden.email}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Hostel Block: {warden.hostel_block}",
    )

    p.showPage()
    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_transfer_list(request):

    transfers = HostelTransfer.objects.select_related(
        "student",
        "from_room",
        "to_room",
    ).order_by("-transfer_date")

    return render(
        request,
        "students/hostel_transfer_list.html",
        {
            "transfers": transfers,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_transfer(request):

    allocations = StudentHostel.objects.select_related(
        "student",
        "room",
    )

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        allocation = StudentHostel.objects.get(
            id=request.POST["allocation"]
        )

        new_room = HostelRoom.objects.get(
            id=request.POST["to_room"]
        )

        # Prevent transferring to the same room
        if allocation.room == new_room:

            messages.error(
                request,
                "Student is already in this room."
            )

            return redirect("add_hostel_transfer")

        # Check room capacity
        if new_room.is_full:

            messages.error(
                request,
                "The selected room is already full."
            )

            return redirect("add_hostel_transfer")

        HostelTransfer.objects.create(

            student=allocation.student,

            from_room=allocation.room,

            to_room=new_room,

            reason=request.POST["reason"],

            transferred_by=request.user,

        )

        allocation.room = new_room

        allocation.save()

        messages.success(
            request,
            "Student transferred successfully."
        )

        return redirect("hostel_transfer_list")

    return render(
        request,
        "students/add_hostel_transfer.html",
        {
            "allocations": allocations,
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_transfer(request, id):

    transfer = get_object_or_404(
        HostelTransfer,
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Transfer_{transfer.student}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Hostel Transfer")

    y = 760

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Student: {transfer.student}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"From Room: {transfer.from_room}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"To Room: {transfer.to_room}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Transfer Date: {transfer.transfer_date}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Reason: {transfer.reason}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Transferred By: {transfer.transferred_by}",
    )

    p.showPage()

    p.save()

    return response

@login_required
@admin_or_bursar
def print_hostel_room(request, id):

    room = get_object_or_404(
        HostelRoom.objects.select_related("block"),
        id=id,
    )

    allocations = room.students.select_related(
        "student",
        "student__school_class",
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Room_{room.room_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL ROOM REPORT",
    )

    y = 690
    p.drawString(
        50,
        y,
        f"Hostel Block : {room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room Number : {room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Capacity : {room.capacity}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Occupied Beds : {room.occupied_beds}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Available Beds : {room.available_beds}",
    )

    y -= 20

    occupancy = 0

    if room.capacity > 0:
        occupancy = round(
            (room.occupied_beds / room.capacity) * 100,
            1,
        )

    p.drawString(
        50,
        y,
        f"Occupancy Rate : {occupancy}%",
    )

    y -= 40

    # ---------------------------------------
    # STUDENTS
    # ---------------------------------------

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        50,
        y,
        "Students in this Room",
    )

    y -= 25

    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y, "No")
    p.drawString(80, y, "Admission")
    p.drawString(160, y, "Student Name")
    p.drawString(340, y, "Class")
    p.drawString(450, y, "Bed")

    y -= 10

    p.line(50, y, 550, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for index, allocation in enumerate(allocations, start=1):

        student = allocation.student

        p.drawString(
            50,
            y,
            str(index),
        )

        p.drawString(
            80,
            y,
            student.admission_number,
        )

        p.drawString(
            160,
            y,
            f"{student.first_name} {student.last_name}",
        )

        p.drawString(
            340,
            y,
            str(student.school_class),
        )

        p.drawString(
            450,
            y,
            str(allocation.bed_number),
        )

        y -= 18

        # Start a new page if needed
        if y < 60:

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL ROOM REPORT",
            )

            y = 690

            p.setFont("Helvetica-Bold", 10)

            p.drawString(50, y, "No")
            p.drawString(80, y, "Admission")
            p.drawString(160, y, "Student Name")
            p.drawString(340, y, "Class")
            p.drawString(450, y, "Bed")

            y -= 10

            p.line(50, y, 550, y)

            y -= 18

            p.setFont("Helvetica", 10)

   # ---------------------------------------
    # FOOTER
    # ---------------------------------------

    draw_school_footer(
        p,
        request,
    )

    p.setFont("Helvetica-Bold", 10)

    p.drawRightString(
        550,
        55,
        f"Total Students: {room.occupied_beds}",
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_occupancy_report(request):

    blocks = HostelBlock.objects.filter(active=True)

    selected_block = None
    rooms = []

    total_rooms = 0
    total_capacity = 0
    total_occupied = 0
    total_available = 0
    occupancy_rate = 0

    if "block" in request.GET:

        selected_block = get_object_or_404(
            HostelBlock,
            id=request.GET["block"],
        )

        rooms = HostelRoom.objects.filter(
            block=selected_block
        )

        total_rooms = rooms.count()

        for room in rooms:

            total_capacity += room.capacity
            total_occupied += room.occupied_beds
            total_available += room.available_beds

        if total_capacity > 0:

            occupancy_rate = round(
                (total_occupied / total_capacity) * 100,
                1,
            )

    return render(
        request,
        "students/hostel_occupancy_report.html",
        {
            "blocks": blocks,
            "selected_block": selected_block,
            "rooms": rooms,
            "total_rooms": total_rooms,
            "total_capacity": total_capacity,
            "total_occupied": total_occupied,
            "total_available": total_available,
            "occupancy_rate": occupancy_rate,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_occupancy_report(request, id):

    block = get_object_or_404(
        HostelBlock,
        id=id,
    )

    rooms = HostelRoom.objects.filter(
        block=block
    ).order_by("room_number")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Occupancy_{block.name}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL OCCUPANCY REPORT",
    )

    y = 690

    total_rooms = rooms.count()
    total_capacity = 0
    total_occupied = 0
    total_available = 0

    for room in rooms:

        total_capacity += room.capacity
        total_occupied += room.occupied_beds
        total_available += room.available_beds

    occupancy_rate = 0

    if total_capacity > 0:

        occupancy_rate = round(
            (total_occupied / total_capacity) * 100,
            1,
        )

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        50,
        y,
        f"Hostel Block : {block.name}",
    )

    y -= 25

    p.setFont("Helvetica", 11)

    p.drawString(
        50,
        y,
        f"Total Rooms : {total_rooms}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Total Capacity : {total_capacity}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Occupied Beds : {total_occupied}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Available Beds : {total_available}",
    )

    y -= 18

    p.drawString(
        50,
        y,
        f"Occupancy Rate : {occupancy_rate}%",
    )

    y -= 35

    # Table Header

    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y, "Room")

    p.drawString(150, y, "Capacity")

    p.drawString(250, y, "Occupied")

    p.drawString(350, y, "Available")

    p.drawString(460, y, "Status")

    y -= 10

    p.line(50, y, 550, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for room in rooms:

        if room.is_full:
            status = "FULL"
        elif room.occupied_beds == 0:
            status = "EMPTY"
        else:
            status = "AVAILABLE"

        p.drawString(
            50,
            y,
            room.room_number,
        )

        p.drawString(
            150,
            y,
            str(room.capacity),
        )

        p.drawString(
            250,
            y,
            str(room.occupied_beds),
        )

        p.drawString(
            350,
            y,
            str(room.available_beds),
        )

        p.drawString(
            460,
            y,
            status,
        )

        y -= 18

        if y < 70:

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL OCCUPANCY REPORT",
            )

            y = 690

            p.setFont("Helvetica-Bold", 10)

            p.drawString(50, y, "Room")
            p.drawString(150, y, "Capacity")
            p.drawString(250, y, "Occupied")
            p.drawString(350, y, "Available")
            p.drawString(460, y, "Status")

            y -= 10

            p.line(50, y, 550, y)

            y -= 18

            p.setFont("Helvetica", 10)

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

@login_required
@admin_or_bursar
def hostel_bed_list(request):

    beds = HostelBed.objects.select_related(
        "room",
        "room__block",
    ).order_by(
        "room__block__name",
        "room__room_number",
        "bed_number",
    )

    return render(
        request,
        "students/hostel_bed_list.html",
        {
            "beds": beds,
        },
    )

@login_required
@admin_or_bursar
def add_hostel_bed(request):

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        HostelBed.objects.create(

            room=room,

            bed_number=request.POST["bed_number"],

        )

        messages.success(
            request,
            "Bed added successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/add_hostel_bed.html",
        {
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def edit_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed,
        id=id,
    )

    rooms = HostelRoom.objects.select_related("block")

    if request.method == "POST":

        bed.room = HostelRoom.objects.get(
            id=request.POST["room"]
        )

        bed.bed_number = request.POST["bed_number"]

        bed.save()

        messages.success(
            request,
            "Bed updated successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/edit_hostel_bed.html",
        {
            "bed": bed,
            "rooms": rooms,
        },
    )

@login_required
@admin_or_bursar
def delete_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed,
        id=id,
    )

    if request.method == "POST":

        bed.delete()

        messages.success(
            request,
            "Bed deleted successfully."
        )

        return redirect("hostel_bed_list")

    return render(
        request,
        "students/delete_hostel_bed.html",
        {
            "bed": bed,
        },
    )

@login_required
@admin_or_bursar
def generate_hostel_beds(request, id):

    room = get_object_or_404(
        HostelRoom,
        id=id,
    )

    created = 0

    for number in range(1, room.capacity + 1):

        bed_number = f"Bed {number}"

        bed, was_created = HostelBed.objects.get_or_create(
            room=room,
            bed_number=bed_number,
        )

        if was_created:
            created += 1

    messages.success(
        request,
        f"{created} bed(s) generated successfully."
    )

    return redirect("hostel_room_list")

@login_required
@admin_or_bursar
def print_hostel_bed(request, id):

    bed = get_object_or_404(
        HostelBed.objects.select_related(
            "room",
            "room__block",
        ),
        id=id,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Bed_{bed.bed_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL BED REPORT",
    )

    y = 690

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Hostel Block : {bed.room.block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room : {bed.room.room_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Bed : {bed.bed_number}",
    )

    y -= 20

    status = "Occupied" if bed.occupied else "Available"

    p.drawString(
        50,
        y,
        f"Status : {status}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

from django.http import JsonResponse

@login_required
@admin_or_bursar
def available_beds(request, room_id):

    beds = HostelBed.objects.filter(
        room_id=room_id,
        occupied=False,
    )

    data = []

    for bed in beds:

        data.append({

            "id": bed.id,

            "name": bed.bed_number,

        })

    return JsonResponse(
        data,
        safe=False,
    )

@login_required
@admin_or_bursar
def hostel_dashboard(request):

    blocks = HostelBlock.objects.prefetch_related(
        "rooms__beds",
        "rooms__students",
        "wardens",
    )

    dashboard = []

    total_rooms = 0
    total_beds = 0
    occupied_beds = 0

    for block in blocks:

        block_rooms = block.rooms.all()

        room_count = block_rooms.count()

        bed_count = 0
        occupied = 0

        for room in block_rooms:

            beds = room.beds.count()

            occupied_room = room.students.count()

            bed_count += beds

            occupied += occupied_room

        available = bed_count - occupied

        percentage = 0

        if bed_count:

            percentage = round(
                (occupied / bed_count) * 100,
                1,
            )

        dashboard.append({

            "block": block,

            "rooms": room_count,

            "beds": bed_count,

            "occupied": occupied,

            "available": available,

            "percentage": percentage,

        })

        total_rooms += room_count
        total_beds += bed_count
        occupied_beds += occupied

    total_available = total_beds - occupied_beds

    overall = 0

    if total_beds:

        overall = round(
            occupied_beds / total_beds * 100,
            1,
        )

    return render(

        request,

        "students/hostel_dashboard.html",

        {

            "dashboard": dashboard,

            "total_rooms": total_rooms,

            "total_beds": total_beds,

            "occupied_beds": occupied_beds,

            "available_beds": total_available,

            "overall": overall,

        },

    )

@login_required
@admin_or_bursar
def print_hostel_dashboard(request):

    blocks = HostelBlock.objects.prefetch_related(
        "rooms__beds",
        "rooms__students",
        "wardens",
    )

    total_rooms = 0
    total_beds = 0
    occupied_beds = 0

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="Hostel_Dashboard.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL OCCUPANCY DASHBOARD",
    )

    y = 690

    dashboard = []

    for block in blocks:

        rooms = block.rooms.all()

        room_count = rooms.count()

        bed_count = 0
        occupied = 0

        for room in rooms:

            bed_count += room.beds.count()
            occupied += room.students.count()

        available = bed_count - occupied

        percentage = 0

        if bed_count:

            percentage = round(
                occupied * 100 / bed_count,
                1,
            )

        dashboard.append({

            "block": block.name,

            "rooms": room_count,

            "beds": bed_count,

            "occupied": occupied,

            "available": available,

            "percentage": percentage,

        })

        total_rooms += room_count
        total_beds += bed_count
        occupied_beds += occupied

    available_beds = total_beds - occupied_beds

    overall = 0

    if total_beds:

        overall = round(
            occupied_beds * 100 / total_beds,
            1,
        )

    p.setFont("Helvetica-Bold", 11)

    p.drawString(50, y, "OVERALL SUMMARY")

    y -= 25

    p.setFont("Helvetica", 10)

    p.drawString(60, y, f"Total Rooms : {total_rooms}")

    y -= 18

    p.drawString(60, y, f"Total Beds : {total_beds}")

    y -= 18

    p.drawString(60, y, f"Occupied Beds : {occupied_beds}")

    y -= 18

    p.drawString(60, y, f"Available Beds : {available_beds}")

    y -= 18

    p.drawString(60, y, f"Occupancy : {overall}%")

    y -= 35

    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y, "Block")

    p.drawString(180, y, "Rooms")

    p.drawString(240, y, "Beds")

    p.drawString(310, y, "Occupied")

    p.drawString(400, y, "Available")

    p.drawString(500, y, "%")

    y -= 8

    p.line(50, y, 560, y)

    y -= 18

    p.setFont("Helvetica", 10)

    for item in dashboard:

        p.drawString(
            50,
            y,
            item["block"],
        )

        p.drawRightString(
            210,
            y,
            str(item["rooms"]),
        )

        p.drawRightString(
            270,
            y,
            str(item["beds"]),
        )

        p.drawRightString(
            360,
            y,
            str(item["occupied"]),
        )

        p.drawRightString(
            460,
            y,
            str(item["available"]),
        )

        p.drawRightString(
            550,
            y,
            f'{item["percentage"]}%',
        )

        y -= 18

        if y < 70:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL OCCUPANCY DASHBOARD",
            )

            y = 700

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response

