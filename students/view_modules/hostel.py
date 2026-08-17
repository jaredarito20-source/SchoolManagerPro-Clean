from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User



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
from students.models import (
    SchoolProfile,
    Student,
    HostelBlock,
    HostelRoom,
    HostelBed,
    StudentHostel,
    HostelWarden,
    HostelTransfer,
)



@login_required
@admin_or_bursar
def hostel_block_list(request):

    school = request.user.school_user.school

    blocks = HostelBlock.objects.filter(
        school=school
    ).order_by("name")

    return render(
        request,
        "students/hostel_block_list.html",
        {"blocks": blocks},
    )


@login_required
@admin_or_bursar
def add_hostel_block(request):

    school = request.user.school_user.school

    if request.method == "POST":

        HostelBlock.objects.create(
            school=school,
            name=request.POST["name"],
            description=request.POST.get("description", ""),
            is_active="active" in request.POST,
        )

        messages.success(
            request,
            "Hostel block added successfully."
        )

        return redirect("hostel_block_list")

    return render(
        request,
        "students/add_hostel_block.html",
    )


@login_required
@admin_or_bursar
def edit_hostel_block(request, id):

    school = request.user.school_user.school

    block = get_object_or_404(
        HostelBlock,
        id=id,
        school=school,
    )

    if request.method == "POST":

        block.name = request.POST["name"]
        block.description = request.POST.get(
            "description",
            "",
        )
        block.active = "active" in request.POST

        block.save()

        messages.success(
            request,
            "Hostel block updated successfully."
        )

        return redirect("hostel_block_list")

    return render(
        request,
        "students/edit_hostel_block.html",
        {"block": block},
    )


@login_required
@admin_or_bursar
def delete_hostel_block(request, id):

    school = request.user.school_user.school

    block = get_object_or_404(
        HostelBlock,
        id=id,
        school=school,
    )

    if request.method == "POST":

        block.delete()

        messages.success(
            request,
            "Hostel block deleted successfully."
        )

        return redirect("hostel_block_list")

    return render(
        request,
        "students/delete_hostel_block.html",
        {"block": block},
    )

@login_required
@admin_or_bursar
def print_hostel_block(request, id):

    school = request.user.school_user.school

    block = get_object_or_404(
        HostelBlock,
        id=id,
        school=school,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Block_{block.name}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL BLOCK DETAILS",
        school,
    )

    y = 690

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Block Name: {block.name}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Description: {block.description}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Status: {'Active' if block.is_active else 'Inactive'}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def student_hostel_list(request):

    school = request.user.school_user.school

    allocations = StudentHostel.objects.filter(
        school=school,
        is_active=True,
    ).select_related(
        "student",
        "room",
        "room__hostel_block",
    )

    return render(
        request,
        "students/student_hostel_list.html",
        {
            "allocations": allocations,
        },
    )
@login_required
@admin_or_bursar
def add_student_hostel(request):

    school = request.user.school_user.school

    students = Student.objects.filter(
        school=school,
        hostel__isnull=True,
    ).order_by(
        "first_name",
        "last_name",
    )

    rooms = HostelRoom.objects.filter(
        school=school,
    ).select_related(
        "hostel_block"
    ).order_by(
        "hostel_block__name",
        "room_number",
    )

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"],
            school=school,
        )

        room = get_object_or_404(
            HostelRoom,
            id=request.POST["room"],
            school=school,
        )

        bed = get_object_or_404(
            HostelBed,
            id=request.POST["bed"],
            school=school,
            room=room,
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
            school=school,
            student=student,
            room=room,
            bed=bed,
        )

        bed.occupied = True
        bed.save(update_fields=["occupied"])

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

    school = request.user.school_user.school

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
        school=school,
    )

    rooms = HostelRoom.objects.filter(
        school=school,
    ).select_related(
        "hostel_block"
    ).order_by(
        "hostel_block__name",
        "room_number",
    )

    if request.method == "POST":

        new_room = get_object_or_404(
            HostelRoom,
            id=request.POST["room"],
            school=school,
        )

        new_bed = get_object_or_404(
            HostelBed,
            id=request.POST["bed"],
            school=school,
            room=new_room,
        )

        # Current allocated bed
        old_bed = allocation.bed

        # If selecting a different occupied bed
        if (
            new_bed.occupied
            and new_bed != old_bed
        ):

            messages.error(
                request,
                "Selected bed is already occupied."
            )

            return redirect(
                "edit_student_hostel",
                id=id,
            )

        # Free old bed
        if old_bed and old_bed != new_bed:
            old_bed.occupied = False
            old_bed.save(
                update_fields=["occupied"]
            )

        # Occupy new bed
        new_bed.occupied = True
        new_bed.save(
            update_fields=["occupied"]
        )

        # Update allocation
        allocation.room = new_room
        allocation.bed = new_bed

        allocation.save(
            update_fields=[
                "room",
                "bed",
            ]
        )

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

    school = request.user.school_user.school

    allocation = get_object_or_404(
        StudentHostel,
        id=id,
        school=school,
    )

    if request.method == "POST":

        bed = allocation.bed

        if bed:
            bed.occupied = False
            bed.save(
                update_fields=["occupied"]
            )

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

    school = request.user.school_user.school

    allocation = get_object_or_404(
        StudentHostel.objects.select_related(
            "student",
            "student__school_class",
            "room",
            "room__hostel_block",
            "bed",
        ),
        id=id,
        school=school,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Allocation_'
        f'{allocation.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    draw_school_header(
        p,
        "HOSTEL ALLOCATION",
        school,
    )

    y = 690

    p.setFont("Helvetica", 10)

    p.drawString(
        50,
        y,
        f"Admission Number : "
        f"{allocation.student.admission_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Student : "
        f"{allocation.student.first_name} "
        f"{allocation.student.last_name}",
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
        f"Hostel Block : "
        f"{allocation.room.hostel_block.name}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Room : {allocation.room.room_number}",
    )

    y -= 20

    # Bed may be missing on an old allocation
    bed_number = (
        allocation.bed.bed_number
        if allocation.bed
        else "Not Assigned"
    )

    p.drawString(
        50,
        y,
        f"Bed : {bed_number}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Assigned : {allocation.admission_date}",
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Status : "
        f"{'Active' if allocation.is_active else 'Inactive'}",
    )

    draw_school_footer(
        p,
        request,
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def hostel_warden_list(request):

    school = request.user.school_user.school

    wardens = HostelWarden.objects.filter(
        school=school
    ).select_related(
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

    school = request.user.school_user.school

    hostel_blocks = HostelBlock.objects.filter(
        school=school,
        is_active=True,
    )

    if request.method == "POST":

        hostel_block = get_object_or_404(
            HostelBlock,
            id=request.POST["hostel_block"],
            school=school,
            is_active=True,
        )

        HostelWarden.objects.create(
            school=school,

            first_name=request.POST["first_name"],

            last_name=request.POST["last_name"],

            gender=request.POST["gender"],

            phone=request.POST.get("phone", ""),

            email=request.POST.get("email", ""),

            hostel_block=hostel_block,

            is_active="active" in request.POST,
        )

        messages.success(
            request,
            "Hostel warden added successfully.",
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

    school = request.user.school_user.school

    warden = get_object_or_404(
        HostelWarden,
        id=id,
        school=school,
    )

    hostel_blocks = HostelBlock.objects.filter(
        school=school,
        is_active=True,
    )

    if request.method == "POST":

        hostel_block = get_object_or_404(
            HostelBlock,
            id=request.POST["hostel_block"],
            school=school,
            is_active=True,
        )

        warden.first_name = request.POST["first_name"]
        warden.last_name = request.POST["last_name"]
        warden.gender = request.POST["gender"]
        warden.phone = request.POST.get("phone", "")
        warden.email = request.POST.get("email", "")
        warden.hostel_block = hostel_block
        warden.is_active = "active" in request.POST

        warden.save()

        messages.success(
            request,
            "Hostel warden updated successfully.",
        )

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

    school = request.user.school_user.school

    warden = get_object_or_404(
        HostelWarden,
        id=id,
        school=school,
    )

    if request.method == "POST":

        warden.delete()

        messages.success(
            request,
            "Hostel warden deleted successfully.",
        )

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

    school = request.user.school_user.school

    warden = get_object_or_404(
        HostelWarden.objects.select_related(
            "hostel_block",
        ),
        id=id,
        school=school,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Warden_{warden.first_name}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 16)

    p.drawString(
        170,
        800,
        "Hostel Warden Details",
    )

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
        f"Hostel Block: {warden.hostel_block.name}",
    )

    y -= 30

    p.drawString(
        50,
        y,
        f"Status: {'Active' if warden.is_active else 'Inactive'}",
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def hostel_transfer_list(request):

    school = request.user.school_user.school
    transfers = HostelTransfer.objects.filter(
        school=school,
    ).select_related(
        "student",
        "from_room",
        "to_room",
    ).order_by(
        "-transfer_date"
    )

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

    school = request.user.school_user.school

    allocations = StudentHostel.objects.filter(
        school=school,
        is_active=True,
    ).select_related(
        "student",
        "room",
        "room__hostel_block",
        "bed",
    )

    rooms = HostelRoom.objects.filter(
        school=school,
    ).select_related(
        "hostel_block",
    )

    if request.method == "POST":

        allocation = get_object_or_404(
            StudentHostel,
            id=request.POST["allocation"],
            school=school,
            is_active=True,
        )

        new_room = get_object_or_404(
            HostelRoom,
            id=request.POST["to_room"],
            school=school,
        )

        # Prevent transferring to the same room
        if allocation.room_id == new_room.id:

            messages.error(
                request,
                "Student is already in this room.",
            )

            return redirect(
                "add_hostel_transfer"
            )

        # Find an available bed in the new room
        new_bed = (
            HostelBed.objects.filter(
                school=school,
                room=new_room,
                occupied=False,
            )
            .order_by("bed_number")
            .first()
        )

        if not new_bed:

            messages.error(
                request,
                "The selected room has no available beds.",
            )

            return redirect(
                "add_hostel_transfer"
            )

        old_bed = allocation.bed

        # Create transfer record
        HostelTransfer.objects.create(
            school=school,
            student=allocation.student,
            from_room=allocation.room,
            to_room=new_room,
            reason=request.POST.get(
                "reason",
                "",
            ),
            transferred_by=request.user,
        )

        # Free old bed
        if old_bed:
            old_bed.occupied = False
            old_bed.save(
                update_fields=["occupied"]
            )

        # Occupy new bed
        new_bed.occupied = True
        new_bed.save(
            update_fields=["occupied"]
        )

        # Update student allocation
        allocation.room = new_room
        allocation.bed = new_bed

        allocation.save(
            update_fields=[
                "room",
                "bed",
            ]
        )

        messages.success(
            request,
            "Student transferred successfully.",
        )

        return redirect(
            "hostel_transfer_list"
        )

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

    school = request.user.school_user.school
    transfer = get_object_or_404(
        HostelTransfer.objects.select_related(
            "student",
            "from_room",
            "to_room",
            "transferred_by",
        ),
        id=id,
        school=school,
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="Hostel_Transfer_{transfer.student.admission_number}.pdf"'
    )

    p = canvas.Canvas(response)

    # School header
    draw_school_header(
        p,
        "HOSTEL TRANSFER",
        school,
    )

    y = 690

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
        f"Admission Number: {transfer.student.admission_number}",
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

    draw_school_footer(
        p,
        request,
    )

    p.showPage()
    p.save()

    return response
@login_required
@admin_or_bursar
def hostel_room_list(request):

    school = request.user.school_user.school

    rooms = HostelRoom.objects.filter(
            school=school
        ).select_related(
            "hostel_block"
        )
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

    school = request.user.school_user.school

    blocks = HostelBlock.objects.filter(
        school=school,
        is_active=True,
    )

    if request.method == "POST":

        block = get_object_or_404(
            HostelBlock,
            id=request.POST["block"],
            school=school,
            is_active=True,
        )

        room = HostelRoom.objects.create(
            school=school,
            hostel_block=block,
            room_number=request.POST["room_number"],
            capacity=int(request.POST["capacity"]),
        )

        # Automatically create beds
        for number in range(1, room.capacity + 1):

            HostelBed.objects.create(
                school=school,
                room=room,
                bed_number=f"Bed {number}",
            )

        messages.success(
            request,
            f"Room {room.room_number} created with "
            f"{room.capacity} beds."
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

    school = request.user.school_user.school

    room = get_object_or_404(
        HostelRoom,
        id=id,
        school=school,
    )

    blocks = HostelBlock.objects.filter(
        school=school,
        is_active=True,
    )

    if request.method == "POST":

        block = get_object_or_404(
            HostelBlock,
            id=request.POST["block"],
            school=school,
            is_active=True,
        )

        new_capacity = int(request.POST["capacity"])

        occupied_beds = HostelBed.objects.filter(
            room=room,
            school=school,
            occupied=True,
        ).count()

        if new_capacity < occupied_beds:

            messages.error(
                request,
                f"Capacity cannot be reduced below "
                f"{occupied_beds} occupied beds."
            )

            return redirect(
                "edit_hostel_room",
                id=room.id,
            )

        room.hostel_block = block
        room.room_number = request.POST["room_number"]

        old_capacity = room.capacity
        room.capacity = new_capacity

        room.save()

        # Capacity increased
        if new_capacity > old_capacity:

            for number in range(
                old_capacity + 1,
                new_capacity + 1
            ):

                HostelBed.objects.create(
                    school=school,
                    room=room,
                    bed_number=f"Bed {number}",
                )

        # Capacity reduced
        elif new_capacity < old_capacity:

            excess = old_capacity - new_capacity

            beds_to_remove = HostelBed.objects.filter(
                room=room,
                school=school,
                occupied=False,
            ).order_by("-id")

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

    school = request.user.school_user.school

    room = get_object_or_404(
        HostelRoom,
        id=id,
        school=school,
    )

    if request.method == "POST":

        room.delete()

        messages.success(
            request,
            "Hostel room deleted successfully."
        )

        return redirect("hostel_room_list")

    return render(
        request,
        "students/delete_hostel_room.html",
        {
            "room": room,
        },
    )

@login_required
@admin_or_bursar
def print_hostel_room(request, id):

    school = request.user.school_user.school

    room = get_object_or_404(
        HostelRoom.objects.select_related(
            "hostel_block",
        ),
        id=id,
        school=school,
    )

    allocations = room.students.filter(
        school=school,
        is_active=True,
    ).select_related(
        "student",
        "student__school_class",
        "bed",
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
        school,
    )

    y = 690

    p.setFont("Helvetica", 10)

    p.drawString(
        50,
        y,
        f"Hostel Block : {room.hostel_block.name}",
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

    for index, allocation in enumerate(
        allocations,
        start=1,
    ):

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
            str(allocation.bed.bed_number),
        )

        y -= 18

        # ---------------------------------------
        # NEW PAGE
        # ---------------------------------------

        if y < 60:

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL ROOM REPORT",
                school,
            )

            y = 690

            p.setFont(
                "Helvetica-Bold",
                10,
            )

            p.drawString(50, y, "No")
            p.drawString(80, y, "Admission")
            p.drawString(160, y, "Student Name")
            p.drawString(340, y, "Class")
            p.drawString(450, y, "Bed")

            y -= 10

            p.line(
                50,
                y,
                550,
                y,
            )

            y -= 18

            p.setFont(
                "Helvetica",
                10,
            )

    # ---------------------------------------
    # FOOTER
    # ---------------------------------------

    draw_school_footer(
        p,
        request,
    )

    p.setFont(
        "Helvetica-Bold",
        10,
    )

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

    school = request.user.school_user.school

    blocks = HostelBlock.objects.filter(
        school=school,
        is_active=True,
    )

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
            school=school,
            is_active=True,
        )

        rooms = HostelRoom.objects.filter(
            school=school,
            hostel_block=selected_block,
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

    school = request.user.school_user.school

    block = get_object_or_404(
        HostelBlock,
        id=id,
        school=school,
        is_active=True,
    )

    rooms = HostelRoom.objects.filter(
        school=school,
        hostel_block=block,
    ).order_by(
        "room_number"
    )

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
        school,
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

    # ---------------------------------------
    # TABLE HEADER
    # ---------------------------------------

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

        # ---------------------------------------
        # NEW PAGE
        # ---------------------------------------

        if y < 70:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL OCCUPANCY REPORT",
                school,
            )

            y = 690

            p.setFont(
                "Helvetica-Bold",
                10,
            )

            p.drawString(50, y, "Room")
            p.drawString(150, y, "Capacity")
            p.drawString(250, y, "Occupied")
            p.drawString(350, y, "Available")
            p.drawString(460, y, "Status")

            y -= 10

            p.line(
                50,
                y,
                550,
                y,
            )

            y -= 18

            p.setFont(
                "Helvetica",
                10,
            )

    # ---------------------------------------
    # FOOTER
    # ---------------------------------------

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response
@login_required
@admin_or_bursar
def hostel_bed_list(request):

    school = request.user.school_user.school

    beds = HostelBed.objects.filter(
        school=school
    ).select_related(
        "room",
        "room__hostel_block",
    ).order_by(
        "room__hostel_block__name",
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

    school = request.user.school_user.school

    rooms = HostelRoom.objects.filter(
        school=school,
    ).select_related(
        "hostel_block",
    )

    if request.method == "POST":

        room = get_object_or_404(
            HostelRoom,
            id=request.POST["room"],
            school=school,
        )

        bed_number = request.POST["bed_number"].strip()

        if not bed_number:
            messages.error(
                request,
                "Bed number is required.",
            )

            return redirect(
                "add_hostel_bed"
            )

        # Prevent duplicate bed numbers in the same room
        if HostelBed.objects.filter(
            school=school,
            room=room,
            bed_number=bed_number,
        ).exists():

            messages.error(
                request,
                f"Bed {bed_number} already exists in this room.",
            )

            return redirect(
                "add_hostel_bed"
            )

        # Do not allow beds beyond room capacity
        existing_beds = HostelBed.objects.filter(
            school=school,
            room=room,
        ).count()

        if existing_beds >= room.capacity:

            messages.error(
                request,
                f"Room {room.room_number} already has "
                f"{room.capacity} beds.",
            )

            return redirect(
                "add_hostel_bed"
            )

        HostelBed.objects.create(
            school=school,
            room=room,
            bed_number=bed_number,
        )

        messages.success(
            request,
            "Bed added successfully.",
        )

        return redirect(
            "hostel_bed_list"
        )

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

    school = request.user.school_user.school

    bed = get_object_or_404(
        HostelBed,
        id=id,
        school=school,
    )

    rooms = HostelRoom.objects.filter(
        school=school,
    ).select_related(
        "hostel_block",
    ).order_by(
        "hostel_block__name",
        "room_number",
    )

    if request.method == "POST":

        room = get_object_or_404(
            HostelRoom,
            id=request.POST["room"],
            school=school,
        )

        bed_number = request.POST["bed_number"].strip()

        if not bed_number:

            messages.error(
                request,
                "Bed number is required.",
            )

            return redirect(
                "edit_hostel_bed",
                id=bed.id,
            )

        # Prevent duplicate bed numbers in the same room
        if HostelBed.objects.filter(
            school=school,
            room=room,
            bed_number=bed_number,
        ).exclude(
            id=bed.id,
        ).exists():

            messages.error(
                request,
                f"Bed {bed_number} already exists in this room.",
            )

            return redirect(
                "edit_hostel_bed",
                id=bed.id,
            )

        # If moving the bed to another room,
        # make sure the new room has space.
        if room.id != bed.room_id:

            existing_beds = HostelBed.objects.filter(
                school=school,
                room=room,
            ).exclude(
                id=bed.id,
            ).count()

            if existing_beds >= room.capacity:

                messages.error(
                    request,
                    f"Room {room.room_number} already has "
                    f"{room.capacity} beds.",
                )

                return redirect(
                    "edit_hostel_bed",
                    id=bed.id,
                )

        bed.room = room
        bed.bed_number = bed_number

        bed.save()

        messages.success(
            request,
            "Bed updated successfully.",
        )

        return redirect(
            "hostel_bed_list"
        )

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

    school = request.user.school_user.school

    bed = get_object_or_404(
        HostelBed,
        id=id,
        school=school,
    )

    if request.method == "POST":

        if bed.occupied:

            messages.error(
                request,
                "This bed cannot be deleted because it is currently occupied.",
            )

            return redirect(
                "hostel_bed_list"
            )

        bed.delete()

        messages.success(
            request,
            "Bed deleted successfully.",
        )

        return redirect(
            "hostel_bed_list"
        )

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

    school = request.user.school_user.school

    room = get_object_or_404(
        HostelRoom,
        id=id,
        school=school,
    )

    created = 0

    for number in range(1, room.capacity + 1):

        bed_number = f"Bed {number}"

        bed, was_created = HostelBed.objects.get_or_create(
            school=school,
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

    school = request.user.school_user.school

    bed = get_object_or_404(
        HostelBed.objects.select_related(
            "room",
            "room__hostel_block",
        ),
        id=id,
        school=school,
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
        school,
    )

    y = 690

    p.setFont("Helvetica", 12)

    p.drawString(
        50,
        y,
        f"Hostel Block : {bed.room.hostel_block.name}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Room : {bed.room.room_number}",
    )

    y -= 25

    p.drawString(
        50,
        y,
        f"Bed : {bed.bed_number}",
    )

    y -= 25

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

    p.showPage()
    p.save()

    return response
from django.http import JsonResponse

@login_required
@admin_or_bursar
def available_beds(request, room_id):

    school = request.user.school_user.school

    room = get_object_or_404(
        HostelRoom,
        id=room_id,
        school=school,
    )

    beds = HostelBed.objects.filter(
        school=school,
        room=room,
        occupied=False,
    ).order_by("bed_number")

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

    school = request.user.school_user.school

    blocks = (
        HostelBlock.objects
        .filter(school=school)
        .prefetch_related(
            "rooms__beds",
            "wardens",
        )
        .order_by("name")
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

            beds = room.beds.filter(
                school=school
            ).count()

            # TEMPORARILY remove the student calculation
            occupied_room = 0

            bed_count += beds
            occupied += occupied_room

        available = max(
            bed_count - occupied,
            0,
        )

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

    total_available = max(
        total_beds - occupied_beds,
        0,
    )

    overall = 0

    if total_beds:
        overall = round(
            (occupied_beds / total_beds) * 100,
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

    school = request.user.school_user.school

    blocks = (
        HostelBlock.objects
        .filter(school=school)
        .prefetch_related(
            "rooms__beds",
            "wardens",
        )
        .order_by("name")
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
        school,
    )

    y = 690

    dashboard = []

    for block in blocks:

        rooms = block.rooms.all()

        room_count = rooms.count()

        bed_count = 0
        occupied = 0

        for room in rooms:

            bed_count += room.beds.filter(
                school=school
            ).count()

            occupied += StudentHostel.objects.filter(
                school=school,
                room=room,
                is_active=True,
            ).count()

        available = max(
            bed_count - occupied,
            0,
        )

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

    available_beds = max(
        total_beds - occupied_beds,
        0,
    )

    overall = 0

    if total_beds:
        overall = round(
            occupied_beds * 100 / total_beds,
            1,
        )

    # ---------------------------------------
    # OVERALL SUMMARY
    # ---------------------------------------

    p.setFont(
        "Helvetica-Bold",
        11,
    )

    p.drawString(
        50,
        y,
        "OVERALL SUMMARY",
    )

    y -= 25

    p.setFont(
        "Helvetica",
        10,
    )

    p.drawString(
        60,
        y,
        f"Total Rooms : {total_rooms}",
    )

    y -= 18

    p.drawString(
        60,
        y,
        f"Total Beds : {total_beds}",
    )

    y -= 18

    p.drawString(
        60,
        y,
        f"Occupied Beds : {occupied_beds}",
    )

    y -= 18

    p.drawString(
        60,
        y,
        f"Available Beds : {available_beds}",
    )

    y -= 18

    p.drawString(
        60,
        y,
        f"Occupancy : {overall}%",
    )

    y -= 35

    # ---------------------------------------
    # TABLE HEADER
    # ---------------------------------------

    p.setFont(
        "Helvetica-Bold",
        10,
    )

    p.drawString(
        50,
        y,
        "Hostel Block",
    )

    p.drawString(
        180,
        y,
        "Rooms",
    )

    p.drawString(
        240,
        y,
        "Beds",
    )

    p.drawString(
        310,
        y,
        "Occupied",
    )

    p.drawString(
        400,
        y,
        "Available",
    )

    p.drawString(
        500,
        y,
        "%",
    )

    y -= 8

    p.line(
        50,
        y,
        560,
        y,
    )

    y -= 18

    p.setFont(
        "Helvetica",
        10,
    )

    # ---------------------------------------
    # BLOCK DATA
    # ---------------------------------------

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

        # -----------------------------------
        # NEW PAGE
        # -----------------------------------

        if y < 70:

            draw_school_footer(
                p,
                request,
            )

            p.showPage()

            draw_school_header(
                p,
                "HOSTEL OCCUPANCY DASHBOARD",
                school,
            )

            y = 700

            p.setFont(
                "Helvetica-Bold",
                10,
            )

            p.drawString(
                50,
                y,
                "Hostel Block",
            )

            p.drawString(
                180,
                y,
                "Rooms",
            )

            p.drawString(
                240,
                y,
                "Beds",
            )

            p.drawString(
                310,
                y,
                "Occupied",
            )

            p.drawString(
                400,
                y,
                "Available",
            )

            p.drawString(
                500,
                y,
                "%",
            )

            y -= 8

            p.line(
                50,
                y,
                560,
                y,
            )

            y -= 18

            p.setFont(
                "Helvetica",
                10,
            )

    draw_school_footer(
        p,
        request,
    )

    p.save()

    return response