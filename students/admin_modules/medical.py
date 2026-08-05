from django.contrib import admin
from students.models import *

admin.site.register(MedicalVisit)
admin.site.register(Medication)
admin.site.register(Prescription)
admin.site.register(HospitalReferral)