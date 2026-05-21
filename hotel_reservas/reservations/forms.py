from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from rooms.models import Room

from .models import Payment, Reservation


def luhn_is_valid(number: str) -> bool:
    total = 0
    reverse_digits = list(reversed(number))
    for idx, digit in enumerate(reverse_digits):
        n = int(digit)
        if idx % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["guests_count", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class PaymentSimulationForm(forms.Form):
    card_number = forms.CharField(label="Numero de tarjeta", max_length=19)
    card_holder = forms.CharField(label="Titular", max_length=80)
    expiry = forms.CharField(label="Vencimiento (MM/YY)", max_length=5)
    cvv = forms.CharField(label="CVV", max_length=4)

    def clean_card_number(self):
        raw = self.cleaned_data["card_number"].replace(" ", "")
        if not raw.isdigit():
            raise ValidationError("La tarjeta solo puede contener digitos.")
        if not 13 <= len(raw) <= 19:
            raise ValidationError("El numero de tarjeta no es valido.")
        if not luhn_is_valid(raw):
            raise ValidationError("El numero de tarjeta no es valido.")
        return raw

    def clean_cvv(self):
        cvv = self.cleaned_data["cvv"].strip()
        if not cvv.isdigit() or len(cvv) not in (3, 4):
            raise ValidationError("El CVV no es valido.")
        return cvv

    def clean_expiry(self):
        expiry = self.cleaned_data["expiry"].strip()
        if "/" not in expiry:
            raise ValidationError("Formato de vencimiento invalido.")
        parts = expiry.split("/")
        if len(parts) != 2:
            raise ValidationError("Formato de vencimiento invalido.")
        month_str, year_str = parts
        if not (month_str.isdigit() and year_str.isdigit()):
            raise ValidationError("Formato de vencimiento invalido.")
        month = int(month_str)
        year = int(year_str)
        if month < 1 or month > 12:
            raise ValidationError("Mes de vencimiento invalido.")
        year += 2000
        today = date.today()
        if (year, month) < (today.year, today.month):
            raise ValidationError("La tarjeta esta vencida.")
        return expiry

    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get("card_number")
        if card_number:
            cleaned_data["card_last4"] = card_number[-4:]
            cleaned_data.pop("card_number", None)
        return cleaned_data


class ReservationCancelForm(forms.Form):
    reason = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"rows": 4}),
    )


class AdminReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}


class ReservationFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "Todos")] + list(Reservation.Status.choices),
        required=False,
    )
    fecha_desde = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    fecha_hasta = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    room = forms.ModelChoiceField(queryset=Room.objects.all(), required=False)
    guest_query = forms.CharField(label="Huesped", required=False)
