from django.shortcuts import render
from django.contrib import messages
from students.decorators import (
    admin_or_bursar,
    admin_or_teacher,
    admin_teacher_secretary,
    in_group,
    admin_required,
    
)
from django.contrib.auth.decorators import login_required



@login_required
@admin_required
def generate_timetable(request):

    if request.method == "POST":

        messages.success(
            request,
            "Timetable generation will be implemented in the next step."
        )

    return render(
        request,
        "timetable/generate_timetable.html"
    )