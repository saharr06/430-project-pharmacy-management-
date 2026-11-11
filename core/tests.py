from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Medication

class MedicationTests(TestCase):
    def setUp(self):
        self.med = Medication.objects.create(name="Paracetamol", quantity=3, minimum_quantity=5, price=Decimal("2.50"), expiry_date=timezone.localdate() + timedelta(days=10), location="A1")

    def test_low_stock_at_threshold(self):
        self.assertTrue(self.med.is_low_stock)
        self.med.quantity = 5
        self.assertTrue(self.med.is_low_stock)
        self.med.quantity = 6
        self.assertFalse(self.med.is_low_stock)

    def test_expiry_boundaries(self):
        self.assertTrue(self.med.is_near_expiry)
        self.med.expiry_date = timezone.localdate() - timedelta(days=1)
        self.assertTrue(self.med.is_expired)
        self.assertFalse(self.med.is_near_expiry)
        self.med.expiry_date = timezone.localdate() + timedelta(days=15)
        self.assertFalse(self.med.is_near_expiry)

    def test_search(self):
        response = self.client.get(reverse("medication_list"), {"q": "para"})
        self.assertContains(response, "Paracetamol")

    def test_add_medication(self):
        response = self.client.post(reverse("medication_add"), {"name": "Ibuprofen", "quantity": 12, "minimum_quantity": 4, "price": "3.75", "expiry_date": "2027-12-01", "location": "B2"})
        self.assertRedirects(response, reverse("medication_list"))
        self.assertEqual(Medication.objects.count(), 2)

    def test_invalid_negative_quantity(self):
        response = self.client.post(reverse("medication_add"), {"name": "Bad", "quantity": -1, "minimum_quantity": 4, "price": "3.75", "expiry_date": "2027-12-01", "location": "B2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Medication.objects.count(), 1)

    def test_missing_expiry_is_safe(self):
        self.med.expiry_date = None
        self.assertFalse(self.med.is_expired)
        self.assertFalse(self.med.is_near_expiry)
        self.assertIsNone(self.med.days_remaining)
        self.med.save()
        response = self.client.get(reverse("notifications"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_counts_threshold(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Low stock")
        self.assertEqual(response.context["low_count"], 1)
