from django.contrib import admin
from .models import (
    Student,
    Teacher,
    Subject,
    SchoolClass,
    Exam,
    Mark,
    SchoolProfile,
)

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(SchoolClass)
admin.site.register(Exam)
admin.site.register(Mark)
admin.site.register(SchoolProfile)