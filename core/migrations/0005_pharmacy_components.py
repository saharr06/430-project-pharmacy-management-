from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0004_backfill_stock_entries")]
    operations = [
        migrations.CreateModel(name="Patient", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("full_name", models.CharField(max_length=160)),
            ("phone", models.CharField(max_length=30)),
            ("date_of_birth", models.DateField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="PharmacySetting", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("expiry_warning_days", models.PositiveIntegerField(default=14)),
        ]),
        migrations.CreateModel(name="QueueTicket", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("number", models.PositiveIntegerField(unique=True)),
            ("status", models.CharField(choices=[("waiting", "Waiting"), ("called", "Called"), ("skipped", "Skipped"), ("served", "Served")], default="waiting", max_length=12)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering": ["number"]}),
        migrations.CreateModel(name="Allergy", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("substance", models.CharField(max_length=160)),
            ("reaction", models.CharField(max_length=250)),
            ("severity", models.CharField(choices=[("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe")], max_length=12)),
            ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="allergies", to="core.patient")),
        ]),
        migrations.CreateModel(name="Sale", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("pharmacist", models.CharField(max_length=120)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("total", models.DecimalField(decimal_places=2, default=0, max_digits=11)),
            ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales", to="core.patient")),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="SaleLine", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("quantity", models.PositiveIntegerField()),
            ("unit_price", models.DecimalField(decimal_places=2, max_digits=9)),
            ("expiry_date", models.DateField()),
            ("medication", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.medication")),
            ("sale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="core.sale")),
        ]),
    ]
