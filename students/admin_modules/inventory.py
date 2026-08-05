from django.contrib import admin
from students.models import *

admin.site.register(InventoryCategory)
admin.site.register(InventoryItem)
admin.site.register(StockTransaction)