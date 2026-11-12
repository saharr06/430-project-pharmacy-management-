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
        next_year = timezone.localdate() + timedelta(days=365)
        response = self.client.post(reverse("medication_add"), {"name": "Ibuprofen", "quantity": 12, "minimum_quantity": 4, "price": "3.75", "expiry_date": next_year.isoformat(), "location": "B2"})
        self.assertRedirects(response, reverse("medication_list"))
        self.assertEqual(Medication.objects.count(), 2)

    def test_invalid_negative_quantity(self):
        next_year = timezone.localdate() + timedelta(days=365)
        response = self.client.post(reverse("medication_add"), {"name": "Bad", "quantity": -1, "minimum_quantity": 4, "price": "3.75", "expiry_date": next_year.isoformat(), "location": "B2"})
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

    def test_cannot_add_expired_medication(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.post(reverse("medication_add"), {"name": "Old", "quantity": 5, "minimum_quantity": 2, "price": "1.00", "expiry_date": yesterday.isoformat(), "location": "A2"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already expired")
        self.assertEqual(Medication.objects.count(), 1)

    def test_can_add_medication_expiring_today(self):
        today = timezone.localdate()
        response = self.client.post(reverse("medication_add"), {"name": "Today", "quantity": 5, "minimum_quantity": 2, "price": "1.00", "expiry_date": today.isoformat(), "location": "A2"})
        self.assertRedirects(response, reverse("medication_list"))
        self.assertEqual(Medication.objects.count(), 2)

    def test_can_edit_expired_medication_without_changing_date(self):
        old_date = timezone.localdate() - timedelta(days=3)
        self.med.expiry_date = old_date
        self.med.save()
        response = self.client.post(reverse("medication_edit", args=[self.med.pk]), {"name": "Paracetamol", "quantity": 0, "minimum_quantity": 5, "price": "2.50", "expiry_date": old_date.isoformat(), "location": "A1"})
        self.assertRedirects(response, reverse("medication_list"))
        self.med.refresh_from_db()
        self.assertEqual(self.med.quantity, 0)

    def test_cannot_edit_date_to_the_past(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.post(reverse("medication_edit", args=[self.med.pk]), {"name": "Paracetamol", "quantity": 3, "minimum_quantity": 5, "price": "2.50", "expiry_date": yesterday.isoformat(), "location": "A1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already expired")
        self.med.refresh_from_db()
        self.assertNotEqual(self.med.expiry_date, yesterday)


class AssignedFeatureTests(TestCase):
    def setUp(self):
        self.med = Medication.objects.create(name="Test medicine", quantity=5,
            minimum_quantity=5, price="2.50", location="A1")

    def test_alert_boundary_and_restock(self):
        response = self.client.get(reverse("notifications"))
        self.assertEqual(list(response.context["low"]), [self.med])
        self.assertEqual(response.context["stock_alert_count"], 1)
        self.med.quantity = 6
        self.med.save()
        response = self.client.get(reverse("notifications"))
        self.assertEqual(list(response.context["low"]), [])
        self.assertEqual(response.context["stock_alert_count"], 0)
        self.assertContains(response, "No low-stock items.")

    def test_zero_threshold_and_out_of_stock(self):
        self.med.quantity = self.med.minimum_quantity = 0
        self.med.save()
        response = self.client.get(reverse("notifications"))
        self.assertContains(response, "Out of stock")
        self.assertEqual(response.context["stock_alert_count"], 1)

    def test_edit_changes_notification(self):
        response = self.client.post(reverse("medication_edit", args=[self.med.pk]), {
            "name": self.med.name, "quantity": 10, "minimum_quantity": 4,
            "price": "2.50", "expiry_date": "", "location": " a1 "})
        self.assertRedirects(response, reverse("medication_list"))
        self.med.refresh_from_db()
        self.assertEqual(self.med.location, "A1")
        self.assertFalse(self.med.is_low_stock)
        self.assertEqual(self.client.get(reverse("dashboard")).context["low_count"], 0)

    def test_finder_search_and_empty_states(self):
        self.assertEqual(len(self.client.get(reverse("location_finder")).context["medications"]), 0)
        response = self.client.get(reverse("location_finder"), {"q": "  TEST  "})
        self.assertContains(response, 'data-location="A1"')
        self.assertEqual(list(response.context["medications"]), [self.med])
        self.assertContains(self.client.get(reverse("location_finder"), {"q": "missing"}), "No medication found")

    def test_finder_keeps_unavailable_items_identifiable(self):
        self.med.quantity = 0
        self.med.expiry_date = timezone.localdate() - timedelta(days=1)
        self.med.location = "Storage room"
        self.med.save()
        response = self.client.get(reverse("location_finder"), {"q": "Test"})
        self.assertContains(response, "Out of stock")
        self.assertContains(response, "Expired")
        self.assertContains(response, "Storage room")

    def test_medication_name_is_escaped_and_string_works(self):
        self.med.name = '<script>alert(1)</script>'
        self.med.save()
        self.assertEqual(str(self.med), self.med.name)
        response = self.client.get(reverse("location_finder"), {"q": "script"})
        self.assertNotContains(response, self.med.name)
        self.assertContains(response, '&lt;script&gt;')