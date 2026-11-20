from datetime import timedelta
from django.db import transaction
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import MedicationForm, StockEntryForm, StockEntryForm
from .models import Medication, StockEntry, StockEntry
from .services.stock import low_stock_medications


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


def medication_delete(request, pk):
    medication = get_object_or_404(Medication, pk=pk)
    if request.method == "POST":
        medication.delete()
        messages.success(request, "Medication deleted.")
        return redirect("medication_list")
    return render(request, "core/medication_confirm_delete.html", {"medication": medication})


def notifications(request):
    today = timezone.localdate()
    items = Medication.objects.all()
    entries = StockEntry.objects.select_related("medication").filter(quantity__gt=0)
    return render(request, "core/notifications.html", {
        "low": low_stock_medications().order_by("quantity", "name"),
        "near_entries": entries.filter(expiry_date__range=(today, today + timedelta(days=14))).order_by("expiry_date"),
        "expired_entries": entries.filter(expiry_date__lt=today).order_by("expiry_date"),
        "near_legacy": items.filter(stock_entries__isnull=True, expiry_date__range=(today, today + timedelta(days=14))).distinct(),
        "expired_legacy": items.filter(stock_entries__isnull=True, expiry_date__lt=today).distinct(),
    })


def location_finder(request):
    query = request.GET.get("q", "").strip()
    items = Medication.objects.filter(name__icontains=query) if query else Medication.objects.none()
    return render(request, "core/location_finder.html", {"medications": items, "query": query})
def medication_detail(request, pk):
    medication = get_object_or_404(Medication, pk=pk)

    recent_entries = medication.stock_entries.order_by(
        "-received_at", "-id"
    )[:3]

    return render(request, "core/medication_detail.html", {
        "medication": medication,
        "recent_entries": recent_entries,
    })


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