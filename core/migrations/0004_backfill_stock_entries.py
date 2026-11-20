from django.db import migrations


def backfill(apps, schema_editor):
    Medication = apps.get_model("core", "Medication")
    StockEntry = apps.get_model("core", "StockEntry")
    for med in Medication.objects.all():
        if med.quantity > 0 and med.expiry_date and not StockEntry.objects.filter(medication_id=med.pk).exists():
            StockEntry.objects.create(medication_id=med.pk, quantity=med.quantity, expiry_date=med.expiry_date)


class Migration(migrations.Migration):
    dependencies = [("core", "0003_stockentry")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
