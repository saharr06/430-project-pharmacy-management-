from datetime import timedelta
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import MedicationForm, StockEntryForm, PatientForm, AllergyForm, SettingForm
from .models import Medication, StockEntry, Patient, Allergy, Sale, SaleLine, QueueTicket, PharmacySetting
from .services.stock import low_stock_medications
from .permissions import role_required

@role_required("Manager", "Pharmacist", "Receptionist")
def dashboard(request):
    today = timezone.localdate()
    items = Medication.objects.all()
    return render(request, "core/dashboard.html", {
        "total": items.count(),
        "low_count": low_stock_medications().count(),
        "near_count": items.filter(expiry_date__range=(today, today + timedelta(days=14))).count(),
        "expired_count": items.filter(expiry_date__lt=today).count(),
        "recent": items.order_by("name")[:6],
    })

@role_required("Manager", "Pharmacist")
def medication_list(request):
    query = request.GET.get("q", "").strip()

    medications = Medication.objects.all()

    if query:
        today = timezone.localdate()

        medications = medications.filter(
            name__icontains=query,
            quantity__gt=0,
            expiry_date__gte=today
        ).order_by("expiry_date")

    return render(
        request,
        "core/medication_list.html",
        {
            "medications": medications,
            "query": query,
        }
    )

@role_required("Manager")
def medication_create(request):
    form = MedicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            medication = form.save()
            if medication.quantity and medication.expiry_date:
                StockEntry.objects.create(medication=medication, quantity=medication.quantity, expiry_date=medication.expiry_date)
        messages.success(request, "Medication added successfully.")
        return redirect("medication_list")
    return render(request, "core/medication_form.html", {"form": form, "heading": "Add medication"})

@role_required("Manager")
def medication_edit(request, pk):
    medication = get_object_or_404(Medication, pk=pk)
    form = MedicationForm(request.POST or None, instance=medication)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            old_quantity = Medication.objects.select_for_update().get(pk=pk).quantity
            medication = form.save()
            difference = medication.quantity - old_quantity
            if difference > 0:
                if not medication.expiry_date or medication.expiry_date < timezone.localdate():
                    raise ValueError("Use Add New Stock with a valid expiry date to increase quantity.")
                else:
                    StockEntry.objects.create(medication=medication, quantity=difference, expiry_date=medication.expiry_date)
            elif difference < 0:
                remaining = -difference
                for entry in medication.stock_entries.select_for_update().order_by("expiry_date", "id"):
                    removed = min(remaining, entry.quantity)
                    entry.quantity -= removed
                    if entry.quantity:
                        entry.save(update_fields=["quantity"])
                    else:
                        entry.delete()
                    remaining -= removed
                    if remaining == 0:
                        break
            if medication.stock_entries.exists():
                earliest = medication.stock_entries.order_by("expiry_date").first()
                medication.expiry_date = earliest.expiry_date
                medication.save(update_fields=["expiry_date"])
        if form.errors:
            return render(request, "core/medication_form.html", {"form": form, "heading": "Edit medication"})
        messages.success(request, "Medication updated successfully.")
        return redirect("medication_list")
    return render(request, "core/medication_form.html", {"form": form, "heading": "Edit medication"})

@role_required("Manager")
def medication_delete(request, pk):
    medication = get_object_or_404(Medication, pk=pk)
    if request.method == "POST":
        medication.delete()
        messages.success(request, "Medication deleted.")
        return redirect("medication_list")
    return render(request, "core/medication_confirm_delete.html", {"medication": medication})

@role_required("Manager", "Pharmacist")
def notifications(request):
    today = timezone.localdate()
    warning_days = PharmacySetting.current().expiry_warning_days
    items = Medication.objects.all()
    entries = StockEntry.objects.select_related("medication").filter(quantity__gt=0)
    return render(request, "core/notifications.html", {
        "low": low_stock_medications().order_by("quantity", "name"),
        "near_entries": entries.filter(expiry_date__range=(today, today + timedelta(days=warning_days))).order_by("expiry_date"),
        "expired_entries": entries.filter(expiry_date__lt=today).order_by("expiry_date"),
        "near_legacy": items.filter(stock_entries__isnull=True, expiry_date__range=(today, today + timedelta(days=warning_days))).distinct(),
        "expired_legacy": items.filter(stock_entries__isnull=True, expiry_date__lt=today).distinct(),
    })

@role_required("Manager", "Pharmacist")
def location_finder(request):
    query = request.GET.get("q", "").strip()
    items = Medication.objects.filter(name__icontains=query) if query else Medication.objects.none()
    return render(request, "core/location_finder.html", {"medications": items, "query": query})
@role_required("Manager", "Pharmacist")
def medication_add_stock(request, pk):
    medication = get_object_or_404(Medication, pk=pk)
    form = StockEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            medication = Medication.objects.select_for_update().get(pk=pk)
            StockEntry.objects.create(
                medication=medication,
                quantity=form.cleaned_data["quantity"],
                expiry_date=form.cleaned_data["expiry_date"],
            )
            medication.quantity += form.cleaned_data["quantity"]
            earliest = medication.stock_entries.order_by("expiry_date").first()
            medication.expiry_date = earliest.expiry_date
            medication.save(update_fields=["quantity", "expiry_date"])
        messages.success(request, "New stock received successfully.")
        return redirect("medication_detail", pk=pk)
    return render(request, "core/add_stock.html", {"medication": medication, "form": form})
@role_required("Manager", "Pharmacist")
def medication_detail(request, pk):
    medication = get_object_or_404(Medication, pk=pk)

    recent_entries = StockEntry.objects.filter(
        medication=medication
    ).order_by("-received_at", "-id")[:3]

    return render(
        request,
        "core/medication_detail.html",
        {
            "medication": medication,
            "recent_entries": recent_entries,
        }
    )

from decimal import Decimal
from django.db.models import Max, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@role_required("Manager", "Pharmacist", "Receptionist")
def patients(request):
    query = request.GET.get("q", "").strip()
    items = Patient.objects.all().order_by("full_name")
    if query:
        criteria = Q(full_name__icontains=query) | Q(phone__icontains=query)
        if query.isdigit():
            criteria |= Q(pk=int(query))
        items = items.filter(criteria)
    return render(request, "core/patients.html", {"patients": items, "query": query})

@role_required("Manager", "Pharmacist")
def patient_edit(request, pk=None):
    patient = get_object_or_404(Patient, pk=pk) if pk else None
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == "POST" and form.is_valid():
        patient = form.save()
        messages.success(request, "Patient saved.")
        return redirect("patient_detail", pk=patient.pk)
    return render(request, "core/generic_form.html", {"form": form, "heading": "Edit patient" if patient else "Add patient", "back_url": "patients"})

@role_required("Manager", "Pharmacist", "Receptionist")
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, "core/patient_detail.html", {"patient": patient, "allergies": patient.allergies.all(), "sales": patient.sales.prefetch_related("lines__medication")})

@role_required("Manager", "Pharmacist")
def allergy_edit(request, patient_pk, pk=None):
    patient = get_object_or_404(Patient, pk=patient_pk)
    allergy = get_object_or_404(Allergy, pk=pk, patient=patient) if pk else None
    form = AllergyForm(request.POST or None, instance=allergy)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.patient = patient
        obj.save()
        messages.success(request, "Allergy saved.")
        return redirect("patient_detail", pk=patient.pk)
    return render(request, "core/generic_form.html", {"form": form, "heading": f"Allergy for {patient.full_name}", "back_url": "patients"})


@require_POST
@role_required("Manager", "Pharmacist")
def allergy_delete(request, patient_pk, pk):
    allergy = get_object_or_404(Allergy, pk=pk, patient_id=patient_pk)
    allergy.delete()
    return redirect("patient_detail", pk=patient_pk)

@role_required("Manager", "Pharmacist")
def sale_list(request):
    return render(request, "core/sales.html", {"sales": Sale.objects.select_related("patient").all()[:100]})

@role_required("Manager", "Pharmacist")
def sale_create(request):
    patients_list = Patient.objects.order_by("full_name")
    meds = Medication.objects.order_by("name")
    if request.method == "POST":
        try:
            med_id = int(request.POST.get("medication", ""))
            quantity = int(request.POST.get("quantity", ""))
            if quantity < 1:
                raise ValueError("Quantity must be at least 1.")
            pharmacist = request.POST.get("pharmacist", "").strip()
            if not pharmacist:
                raise ValueError("Enter the dispensing pharmacist's name.")
            patient_id = request.POST.get("patient")
            patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None
            with transaction.atomic():
                medication = get_object_or_404(Medication.objects.select_for_update(), pk=med_id)
                today = timezone.localdate()
                # Lock and allocate earliest-expiring usable stock first (FEFO).
                entries = list(StockEntry.objects.select_for_update().filter(
                    medication=medication, quantity__gt=0, expiry_date__gte=today
                ).order_by("expiry_date", "id"))
                available = sum(e.quantity for e in entries)
                if available < quantity:
                    raise ValueError(f"Only {available} unexpired units are available.")
                if patient:
                    terms = [a.substance.lower().strip() for a in patient.allergies.all()]
                    if any(term and term in medication.name.lower() for term in terms):
                        raise ValueError("Potential patient allergy detected. Sale blocked; review allergy record.")
                sale = Sale.objects.create(patient=patient, pharmacist=pharmacist)
                remaining = quantity
                for entry in entries:
                    take = min(remaining, entry.quantity)
                    if take == 0:
                        continue
                    SaleLine.objects.create(sale=sale, medication=medication, quantity=take,
                                            unit_price=medication.price, expiry_date=entry.expiry_date)
                    entry.quantity -= take
                    if entry.quantity:
                        entry.save(update_fields=["quantity"])
                    else:
                        entry.delete()
                    remaining -= take
                    if not remaining:
                        break
                medication.quantity = sum(e.quantity for e in StockEntry.objects.filter(medication=medication))
                earliest = medication.stock_entries.order_by("expiry_date").first()
                medication.expiry_date = earliest.expiry_date if earliest else None
                medication.save(update_fields=["quantity", "expiry_date"])
                sale.total = medication.price * quantity
                sale.save(update_fields=["total"])
            messages.success(request, f"Sale #{sale.pk} completed. Total: {sale.total}")
            return redirect("sale_detail", pk=sale.pk)
        except (ValueError, TypeError) as exc:
            messages.error(request, str(exc))
    return render(request, "core/sale_form.html", {"patients": patients_list, "medications": meds})

@role_required("Manager", "Pharmacist")
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("patient").prefetch_related("lines__medication"), pk=pk)
    return render(request, "core/sale_detail.html", {"sale": sale})

@role_required("Manager", "Pharmacist", "Receptionist")
def queue_page(request):
    return render(request, "core/queue.html", {"tickets": QueueTicket.objects.order_by("-number")[:40], "current": QueueTicket.objects.filter(status="called").order_by("-number").first()})

@role_required("Manager", "Pharmacist", "Receptionist")
@require_POST
def queue_take(request):
    with transaction.atomic():
        # SQLite serializes writers; unique number protects against collisions.
        next_number = (QueueTicket.objects.aggregate(m=Max("number"))["m"] or 0) + 1
        ticket = QueueTicket.objects.create(number=next_number)
    messages.success(request, f"Your queue number is {ticket.number}.")
    return redirect("queue_page")

@role_required("Manager", "Pharmacist")
@require_POST
def queue_next(request):
    with transaction.atomic():
        QueueTicket.objects.filter(status="called").update(status="served")
        ticket = QueueTicket.objects.filter(status="waiting").order_by("number").first()
        if ticket:
            ticket.status = "called"
            ticket.save(update_fields=["status"])
    return redirect("queue_page")


@require_POST
@role_required("Manager", "Pharmacist")
def queue_skip(request):
    QueueTicket.objects.filter(status="called").update(status="skipped")
    return redirect("queue_page")

@role_required("Manager", "Pharmacist", "Receptionist")
def queue_display(request):
    current = QueueTicket.objects.filter(status="called").order_by("-number").first()
    return render(request, "core/queue_display.html", {"current": current})

@role_required("Manager", "Pharmacist")
def reports(request):
    from django.db.models import F
    from django.http import HttpResponse
    import csv
    today = timezone.localdate()
    days = PharmacySetting.current().expiry_warning_days
    low = Medication.objects.filter(quantity__lte=F("minimum_quantity")).order_by("name")
    expiring = StockEntry.objects.select_related("medication").filter(quantity__gt=0, expiry_date__lte=today + timedelta(days=days)).order_by("expiry_date")
    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pharmacy_report.csv"'
        writer = csv.writer(response)
        writer.writerow(["Type", "Medication", "Quantity", "Expiry", "Location"])
        for med in low:
            writer.writerow(["Low stock", med.name, med.quantity, med.expiry_date, med.location])
        for entry in expiring:
            writer.writerow(["Expired" if entry.expiry_date < today else "Near expiry", entry.medication.name, entry.quantity, entry.expiry_date, entry.medication.location])
        return response
    return render(request, "core/reports.html", {"low": low, "expiring": expiring, "today": today, "days": days})

@role_required("Manager")
def settings_page(request):
    obj = PharmacySetting.current()
    form = SettingForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Settings saved.")
        return redirect("settings_page")
    return render(request, "core/generic_form.html", {"form": form, "heading": "Pharmacy settings", "back_url": "dashboard"})
