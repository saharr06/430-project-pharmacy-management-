from datetime import timedelta
from django.utils import timezone

def is_expired(medication):
    return medication.expiry_date is not None and medication.expiry_date < timezone.localdate()

def is_near_expiry(medication):
    today = timezone.localdate()
    return medication.expiry_date is not None and today <= medication.expiry_date <= today + timedelta(days=14)

def days_remaining(medication):
    if medication.expiry_date is None:
        return None
    return (medication.expiry_date - timezone.localdate()).days
