from django.contrib import admin
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