from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from students.models import (
    SchoolClass,
    SubjectRequirement,
    TeacherAvailability,
    SchoolDay,
    Period,
    Timetable,
)

from students.decorators import admin_required


@login_required
@admin_required
def generate_timetable(request):

    if request.method == "POST":

        # Remove previously generated timetable entries
        Timetable.objects.all().delete()

        classes = SchoolClass.objects.all()
        days = SchoolDay.objects.filter(active=True).order_by("id")
        periods = Period.objects.filter(
            is_break=False
        ).order_by("order")

        generated = 0
        conflicts = []

        for school_class in classes:

            requirements = SubjectRequirement.objects.filter(
                school_class=school_class
            ).select_related(
                "subject"
            )

            for requirement in requirements:

                subject = requirement.subject

                # Find the teacher assigned to this subject
                teacher = getattr(subject, "teacher", None)

                if teacher is None:
                    conflicts.append(
                        f"{school_class} - {subject}: "
                        f"No teacher assigned."
                    )
                    continue

                lessons_needed = requirement.lessons_per_week

                assigned = 0

                for day in days:

                    if assigned >= lessons_needed:
                        break

                    for period in periods:

                        if assigned >= lessons_needed:
                            break

                        # Check class conflict
                        class_busy = Timetable.objects.filter(
                            school_class=school_class,
                            day=day,
                            period=period,
                        ).exists()

                        if class_busy:
                            continue

                        # Check teacher conflict
                        teacher_busy = Timetable.objects.filter(
                            teacher=teacher,
                            day=day,
                            period=period,
                        ).exists()

                        if teacher_busy:
                            continue

                        # Check teacher availability
                        availability = TeacherAvailability.objects.filter(
                            teacher=teacher,
                            day=day,
                            period=period,
                        ).first()

                        if availability and not availability.available:
                            continue

                        # Create lesson
                        Timetable.objects.create(
                            school_class=school_class,
                            day=day,
                            period=period,
                            subject=subject,
                            teacher=teacher,
                        )

                        assigned += 1
                        generated += 1

                if assigned < lessons_needed:

                    conflicts.append(
                        f"{school_class} - {subject}: "
                        f"Required {lessons_needed}, "
                        f"assigned {assigned}."
                    )

        if conflicts:

            messages.warning(
                request,
                f"{generated} lessons generated, "
                f"but {len(conflicts)} conflicts remain."
            )

            request.session["timetable_conflicts"] = conflicts

        else:

            messages.success(
                request,
                f"Timetable generated successfully. "
                f"{generated} lessons created."
            )

        return redirect("generate_timetable")

    return render(
        request,
        "timetable/generate_timetable.html",
    )