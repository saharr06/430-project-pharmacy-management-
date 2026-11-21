from django import forms
from django.utils import timezone
from .models import Medication, Patient, Allergy, PharmacySetting
import re
from django.core.exceptions import ValidationError


class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ["name", "quantity", "minimum_quantity", "price", "expiry_date", "location"]
        widgets = {"expiry_date": forms.DateInput(attrs={"type": "date"})}
        help_texts = {"location": "Example: A2"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiry_date"].required = True
        if not self.instance.pk:
            self.fields["expiry_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_expiry_date(self):
      expiry_date = self.cleaned_data.get("expiry_date")

      if expiry_date is None:
          raise forms.ValidationError(
            "Expiry date is required."
          )

      if expiry_date < timezone.localdate():
          raise forms.ValidationError(
            "Expiry date cannot be in the past."
          )

      return expiry_date
    
    def clean_location(self):
        location = self.cleaned_data["location"].strip().upper()
        if not re.fullmatch(r"[AB][1-9][0-9]*", location):
            raise ValidationError("Location must be A or B followed by a positive number (e.g. A1 or B12).")
        return location


class StockEntryForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        label="New stock quantity"
    )

    expiry_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date"}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["expiry_date"].widget.attrs["min"] = (
            timezone.localdate().isoformat()
        )

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data["expiry_date"]

        if expiry_date < timezone.localdate():
            raise forms.ValidationError(
                "Cannot add expired stock. "
                "Please select today or a future date."
            )

        return expiry_date

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["full_name", "phone", "date_of_birth"]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_of_birth"].widget.attrs["max"] = (
            timezone.localdate().isoformat()
        )

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]

        if dob > timezone.localdate():
            raise forms.ValidationError(
                "Date of birth cannot be in the future."
            )

        return dob


class AllergyForm(forms.ModelForm):
    class Meta:
        model = Allergy
        fields = ["substance", "reaction", "severity"]


class SettingForm(forms.ModelForm):
    class Meta:
        model = PharmacySetting
        fields = ["expiry_warning_days"]
