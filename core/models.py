from django.db import models
from .services import stock, expiry


class Medication(models.Model):
    name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=0)
    minimum_quantity = models.PositiveIntegerField(default=5)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    expiry_date = models.DateField()
    location = models.CharField(max_length=80, help_text="Example: A1 / Shelf 2")
    

    class Meta:
        ordering = ["name", "expiry_date"]

    @property
    def is_low_stock(self):
        return stock.is_low_stock(self)

    @property
    def is_expired(self):
        return expiry.is_expired(self)

    @property
    def is_near_expiry(self):
        return expiry.is_near_expiry(self)

    @property
    def days_remaining(self):
        return expiry.days_remaining(self)

    def __str__(self):
        return self.name

class StockEntry(models.Model):
    medication = models.ForeignKey(
        "Medication",
        on_delete=models.CASCADE,
        related_name="stock_entries"
    )
    quantity = models.PositiveIntegerField()
    expiry_date = models.DateField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expiry_date", "id"]

class Patient(models.Model):
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} (#{self.pk})"


class Allergy(models.Model):
    SEVERITY = [("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe")]
    patient = models.ForeignKey(Patient, related_name="allergies", on_delete=models.CASCADE)
    substance = models.CharField(max_length=160)
    reaction = models.CharField(max_length=250)
    severity = models.CharField(max_length=12, choices=SEVERITY)

    def __str__(self):
        return f"{self.substance} ({self.severity})"


class Sale(models.Model):
    patient = models.ForeignKey(Patient, null=True, blank=True, related_name="sales", on_delete=models.SET_NULL)
    pharmacist = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, related_name="lines", on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=9, decimal_places=2)
    expiry_date = models.DateField()

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class QueueTicket(models.Model):
    STATUS = [("waiting", "Waiting"), ("called", "Called"), ("skipped", "Skipped"), ("served", "Served")]
    number = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=12, choices=STATUS, default="waiting")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]


class PharmacySetting(models.Model):
    expiry_warning_days = models.PositiveIntegerField(default=14)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
