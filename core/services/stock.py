from django.db.models import F


def is_low_stock(medication):
    return medication.quantity <= medication.minimum_quantity


def low_stock_medications():
    from core.models import Medication
    return Medication.objects.filter(quantity__lte=F("minimum_quantity"))
