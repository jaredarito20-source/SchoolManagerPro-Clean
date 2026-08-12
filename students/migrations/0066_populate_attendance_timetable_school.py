
from django.db import migrations


def populate_school(apps, schema_editor):
    Attendance = apps.get_model("students", "Attendance")
    Timetable = apps.get_model("students", "Timetable")

    # --------------------------------
    # ATTENDANCE
    # --------------------------------

    for attendance in Attendance.objects.filter(
        school__isnull=True
    ).select_related("school_class"):

        if attendance.school_class_id:
            attendance.school_id = attendance.school_class.school_id
            attendance.save(
                update_fields=["school"]
            )

    # --------------------------------
    # TIMETABLE
    # --------------------------------

    for timetable in Timetable.objects.filter(
        school__isnull=True
    ).select_related("school_class"):

        if timetable.school_class_id:
            timetable.school_id = timetable.school_class.school_id
            timetable.save(
                update_fields=["school"]
            )


def reverse_populate_school(apps, schema_editor):
    Attendance = apps.get_model("students", "Attendance")
    Timetable = apps.get_model("students", "Timetable")

    Attendance.objects.update(school=None)
    Timetable.objects.update(school=None)


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0065_remove_timetable_unique_class_period_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_school,
            reverse_populate_school,
        ),
    ]

