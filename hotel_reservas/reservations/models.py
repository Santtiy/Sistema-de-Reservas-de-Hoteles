import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
class Reservation(models.Model):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pendiente"
		CONFIRMED = "CONFIRMED", "Confirmada"
		CHECKED_IN = "CHECKED_IN", "Check-in"
		CHECKED_OUT = "CHECKED_OUT", "Check-out"
		CANCELLED = "CANCELLED", "Cancelada"

	guest = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="reservations",
	)
	room = models.ForeignKey(
		"rooms.Room",
		on_delete=models.PROTECT,
		related_name="reservations",
	)
	check_in = models.DateField()
	check_out = models.DateField()
	guests_count = models.PositiveIntegerField()
	total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	status = models.CharField(
		max_length=20, choices=Status.choices, default=Status.PENDING
	)
	confirmation_code = models.CharField(max_length=12, unique=True, blank=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Reserva {self.confirmation_code or 'sin codigo'}"

	def get_absolute_url(self):
		return reverse("reservations:detail", kwargs={"pk": self.pk})

	@property
	def nights(self) -> int:
		if not self.check_in or not self.check_out:
			return 0
		return (self.check_out - self.check_in).days

	def can_be_cancelled(self) -> bool:
		if self.status in {
			self.Status.CANCELLED,
			self.Status.CHECKED_IN,
			self.Status.CHECKED_OUT,
		}:
			return False
		if not self.check_in:
			return False
		limit = timezone.now() + timedelta(hours=48)
		check_in_dt = timezone.make_aware(
			datetime.combine(self.check_in, datetime.min.time())
		)
		return check_in_dt > limit

	def calculate_total(self):
		if not self.room_id:
			return Decimal("0.00")
		base_price = Decimal(str(self.room.room_type.base_price))
		return base_price * Decimal(self.nights)

	def clean(self):
		super().clean()
		if self.check_in and self.check_out and self.check_out <= self.check_in:
			raise ValidationError({"check_out": "La fecha de salida debe ser posterior."})
		if self.check_in and self.check_in < timezone.localdate():
			raise ValidationError({"check_in": "La fecha de ingreso no puede ser pasada."})
		if self.room_id and self.guests_count:
			room = self.room
			if self.guests_count > room.room_type.capacity:
				raise ValidationError(
					{"guests_count": "Supera la capacidad de la habitacion."}
				)
		if self.room_id and self.check_in and self.check_out:
			room = self.room
			if not room.is_available_between(
				self.check_in, self.check_out, exclude_reservation_pk=self.pk
			):
				raise ValidationError("La habitacion no esta disponible en esas fechas.")

	def save(self, *args, **kwargs):
		if not self.confirmation_code:
			code = uuid.uuid4().hex[:8].upper()
			while Reservation.objects.filter(confirmation_code=code).exists():
				code = uuid.uuid4().hex[:8].upper()
			self.confirmation_code = code
		if not self.total_price:
			self.total_price = self.calculate_total()
		super().save(*args, **kwargs)


class Payment(models.Model):
	class Method(models.TextChoices):
		CARD = "CARD", "Tarjeta"
		TRANSFER = "TRANSFER", "Transferencia"
		CASH = "CASH", "Efectivo"

	class Status(models.TextChoices):
		PENDING = "PENDING", "Pendiente"
		COMPLETED = "COMPLETED", "Completado"
		FAILED = "FAILED", "Fallido"
		REFUNDED = "REFUNDED", "Reembolsado"

	reservation = models.OneToOneField(
		Reservation, on_delete=models.CASCADE, related_name="payment"
	)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	method = models.CharField(max_length=20, choices=Method.choices, default=Method.CARD)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	transaction_id = models.CharField(max_length=40, unique=True, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	card_last4 = models.CharField(max_length=4, blank=True)

	def save(self, *args, **kwargs):
		if not self.transaction_id:
			self.transaction_id = uuid.uuid4().hex
		super().save(*args, **kwargs)


class ReservationStatusLog(models.Model):
	reservation = models.ForeignKey(
		Reservation, on_delete=models.CASCADE, related_name="status_logs"
	)
	previous_status = models.CharField(max_length=20)
	new_status = models.CharField(max_length=20)
	changed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
	)
	changed_at = models.DateTimeField(auto_now_add=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-changed_at"]

	def __str__(self) -> str:
		return f"{self.previous_status} -> {self.new_status}"
