from datetime import timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import MedicationForm
from .models import Medication
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
        form.save()
        messages.success(request, "Medication added successfully.")
        return redirect("medication_list")
    return render(request, "core/medication_form.html", {"form": form, "heading": "Add medication"})


def medication_edit(request, pk):
    medication = get_object_or_404(Medication, pk=pk)
    form = MedicationForm(request.POST or None, instance=medication)
    if request.method == "POST" and form.is_valid():
        form.save()
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
    return render(request, "core/notifications.html", {
        "low": low_stock_medications().order_by("quantity", "name"),
        "near": items.filter(expiry_date__range=(today, today + timedelta(days=14))).order_by("expiry_date"),
        "expired": items.filter(expiry_date__lt=today).order_by("expiry_date"),
    })


def location_finder(request):
    query = request.GET.get("q", "").strip()
    items = Medication.objects.filter(name__icontains=query) if query else Medication.objects.none()
    return render(request, "core/location_finder.html", {"medications": items, "query": query})
