from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class RoomType(models.Model):
    """Tipo de habitación: define precio base, capacidad y descripción."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField()
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while RoomType.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class Amenity(models.Model):
    """Servicio o comodidad asociado a una habitación (WiFi, Piscina, etc.)."""

    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=50, help_text="Clase Bootstrap Icons, ej: bi-wifi")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Amenities"

    def __str__(self) -> str:
        return self.name


class Room(models.Model):
    """Habitación física del hotel."""

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Disponible"
        MAINTENANCE = "MAINTENANCE", "Mantenimiento"
        OUT_OF_SERVICE = "OUT_OF_SERVICE", "Fuera de servicio"

    number = models.CharField(max_length=20, unique=True)
    room_type = models.ForeignKey(
        RoomType, on_delete=models.PROTECT, related_name="rooms"
    )
    floor = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    description = models.TextField(blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]

    def __str__(self) -> str:
        return f"Habitación {self.number} - {self.room_type.name}"

    def get_absolute_url(self):
        return reverse("rooms:detail", kwargs={"pk": self.pk})

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()

    def is_available_between(self, check_in, check_out, exclude_reservation_pk=None) -> bool:
        """True si no hay reservas no-canceladas solapadas con el rango."""
        if self.status != self.Status.AVAILABLE:
            return False
        from reservations.models import Reservation  # import local: evita ciclo

        qs = self.reservations.exclude(status=Reservation.Status.CANCELLED)
        if exclude_reservation_pk:
            qs = qs.exclude(pk=exclude_reservation_pk)
        overlapping = qs.filter(check_in__lt=check_out, check_out__gt=check_in)
        return not overlapping.exists()

    def price_for(self, check_in, check_out) -> Decimal:
        nights = (check_out - check_in).days
        if nights <= 0:
            return Decimal("0.00")
        return self.room_type.base_price * nights


class RoomImage(models.Model):
    """Imagen asociada a una habitación. Se guarda como URL externa."""

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = models.URLField(max_length=500)
    caption = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_main", "id"]

    def __str__(self) -> str:
        return f"Imagen de {self.room} ({'principal' if self.is_main else 'secundaria'})"
