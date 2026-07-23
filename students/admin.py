from django.contrib import admin
from django.contrib.auth.models import Group

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
)

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(SchoolClass)
admin.site.register(Exam)
admin.site.register(Mark)
admin.site.register(SchoolProfile)
admin.site.register(FeeStructure)
admin.site.register(FeePayment)
admin.site.register(Attendance)
admin.site.register(Timetable)

admin.site.site_header = "School Management Administration"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Management"