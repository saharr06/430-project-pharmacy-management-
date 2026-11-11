from django import forms
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
        

    def clean_price(self):
        price = self.cleaned_data["price"]

        if price < 0:
            raise forms.ValidationError(
                "Price cannot be negative."
            )

        return price

    def clean_location(self):
        location = self.cleaned_data["location"].strip()
        if not location:
            raise forms.ValidationError("Enter a shelf location.")
        if location.upper() in {f"{row}{n}" for row in "AB" for n in range(1, 9)}:
            return location.upper()
        return location
