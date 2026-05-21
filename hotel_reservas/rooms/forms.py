from datetime import date

from django import forms
from django.forms import inlineformset_factory

from .models import Amenity, Room, RoomImage, RoomType


class DateInput(forms.DateInput):
    input_type = "date"


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "number",
            "room_type",
            "floor",
            "status",
            "description",
            "amenities",
        ]
        widgets = {
            "amenities": forms.CheckboxSelectMultiple(),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ["name", "description", "base_price", "capacity"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class AmenityForm(forms.ModelForm):
    class Meta:
        model = Amenity
        fields = ["name", "icon"]
        help_texts = {"icon": "Usa una clase de Bootstrap Icons, ej: bi-wifi"}


RoomImageFormSet = inlineformset_factory(
    Room,
    RoomImage,
    fields=["image", "caption", "is_main"],
    extra=3,
    can_delete=True,
)


class RoomSearchForm(forms.Form):
    """Formulario de búsqueda y filtros para el catálogo de habitaciones."""

    check_in = forms.DateField(
        required=False, widget=DateInput(), label="Check-in"
    )
    check_out = forms.DateField(
        required=False, widget=DateInput(), label="Check-out"
    )
    capacity_min = forms.IntegerField(
        required=False, min_value=1, label="Huéspedes mínimo"
    )
    room_type = forms.ModelChoiceField(
        queryset=RoomType.objects.all(),
        required=False,
        label="Tipo",
        empty_label="Todos los tipos",
    )
    price_max = forms.DecimalField(
        required=False, min_value=0, label="Precio máx. por noche"
    )

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError(
                    "La fecha de salida debe ser posterior a la de entrada."
                )
            if check_in < date.today():
                raise forms.ValidationError(
                    "La fecha de entrada no puede ser anterior a hoy."
                )
        return cleaned
