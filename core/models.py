from django.db import models
from .services import stock, expiry

class Medication(models.Model):
    name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=0)
    minimum_quantity = models.PositiveIntegerField(default=5)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
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
