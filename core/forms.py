from django import forms
from django.utils import timezone
from .models import Medication


class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = [
            "name",
            "quantity",
            "minimum_quantity",
            "price",
            "expiry_date",
            "location",
        ]
        widgets = {
            "expiry_date": forms.DateInput(
                attrs={"type": "date"}
            )

        }
        help_texts = {
            "location": "Example: A2",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["expiry_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_price(self):
        price = self.cleaned_data["price"]

        if price < 0:
            raise forms.ValidationError(
                "Price cannot be negative."
            )

        return price

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get("expiry_date")
        if expiry_date is None:
            return expiry_date
        unchanged = self.instance.pk and expiry_date == self.instance.expiry_date
        if expiry_date < timezone.localdate() and not unchanged:
            raise forms.ValidationError(
                "This medication is already expired. Enter today's date or a later one."
            )
        return expiry_date

    def clean_location(self):
        location = self.cleaned_data["location"].strip()
        if not location:
            raise forms.ValidationError("Enter a shelf location.")
        if location.upper() in {f"{row}{n}" for row in "AB" for n in range(1, 9)}:
            return location.upper()
        return location