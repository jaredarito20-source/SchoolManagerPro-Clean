from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *
from .models import TransportRoute



from .models import (
    Student,
    Teacher,
    Subject,
    SchoolClass,
    Exam,
    Mark,
    SchoolProfile,
    FeeStructure,
    FeePayment,
    Attendance,
    Timetable,
    ExamTimetable,
    SalaryStructure,
    Payroll

)

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(SchoolClass)
admin.site.register(Exam)
admin.site.register(Mark)

admin.site.register(FeeStructure)
admin.site.register(FeePayment)
admin.site.register(Attendance)
admin.site.register(Timetable)
admin.site.register(ExamTimetable)

admin.site.register(TransportRoute)
admin.site.register(StudentTransport)



admin.site.register(InventoryCategory)
admin.site.register(InventoryItem)

admin.site.site_header = "School Management Administration"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Management"

@admin.register(SchoolProfile)

class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "current_term",
        "academic_year",
        "phone",
    )

    fieldsets = (
        (
            "School Information",
            {
                "fields": (
                    "name",
                    "motto",
                    "address",
                    "phone",
                    "email",
                    "website",
                    "logo",
                    "school_stamp",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "current_term",
                    "academic_year",
                    "closing_date",
                    "opening_date",
                )
            },
        ),
        (
            "Principal",
            {
                "fields": (
                    "principal_name",
                    "principal_signature",
                )
            },
        ),
    )

