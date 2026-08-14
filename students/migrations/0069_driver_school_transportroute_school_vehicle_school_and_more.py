from django.db import migrations, models
import django.db.models.deletion


def convert_transport_drivers(apps, schema_editor):
    TransportRoute = apps.get_model("students", "TransportRoute")

    # Existing route 1 was using Teacher ID 3.
    # The new Driver record is Driver ID 1.
    #
    # Change the stored foreign-key value BEFORE Django
    # changes the foreign-key constraint to students_driver.

    TransportRoute.objects.filter(
        driver_id=3
    ).update(
        driver_id=1
    )


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0068_examtimetable_school"),
    ]

    operations = [

        # First convert existing Teacher IDs to Driver IDs.
        migrations.RunPython(
            convert_transport_drivers,
            migrations.RunPython.noop,
        ),

        migrations.AddField(
            model_name="driver",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="students.schoolprofile",
            ),
        ),

        migrations.AddField(
            model_name="transportroute",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="students.schoolprofile",
            ),
        ),

        migrations.AddField(
            model_name="vehicle",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="students.schoolprofile",
            ),
        ),

        migrations.AlterField(
            model_name="transportroute",
            name="driver",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="transport_routes",
                to="students.driver",
            ),
        ),
    ]