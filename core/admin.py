from django.contrib import admin
from .models import Medication

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "minimum_quantity", "expiry_date", "location")
    search_fields = ("name",  "location")
