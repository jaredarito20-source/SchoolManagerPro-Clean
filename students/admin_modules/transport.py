from django.contrib import admin
from students.models import *

admin.site.register(TransportRoute)
admin.site.register(Vehicle)
admin.site.register(Driver)
admin.site.register(StudentTransport)