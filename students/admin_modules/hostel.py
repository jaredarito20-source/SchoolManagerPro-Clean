from django.contrib import admin
from students.models import *

admin.site.register(HostelBlock)
admin.site.register(HostelRoom)
admin.site.register(HostelBed)
admin.site.register(StudentHostel)
admin.site.register(HostelTransfer)
admin.site.register(HostelWarden)