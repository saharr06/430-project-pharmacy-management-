from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Medication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("batch_number", models.CharField(max_length=50, unique=True)),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("minimum_quantity", models.PositiveIntegerField(default=5)),
                ("price", models.DecimalField(decimal_places=2, max_digits=9)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("location", models.CharField(help_text="Example: A1 / Shelf 2", max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name", "expiry_date"]},
        ),
    ]
