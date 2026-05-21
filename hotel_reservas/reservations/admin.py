from django.contrib import admin

from .models import Payment, Reservation, ReservationStatusLog


class PaymentInline(admin.StackedInline):
	model = Payment
	extra = 0
	readonly_fields = ("transaction_id", "paid_at")


class ReservationStatusLogInline(admin.TabularInline):
	model = ReservationStatusLog
	extra = 0
	readonly_fields = ("previous_status", "new_status", "changed_by", "changed_at")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = (
		"confirmation_code",
		"guest",
		"room",
		"check_in",
		"check_out",
		"status",
		"total_price",
	)
	list_filter = ("status", "check_in", "check_out")
	search_fields = ("confirmation_code", "guest__username", "guest__email")
	inlines = [PaymentInline, ReservationStatusLogInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ("reservation", "amount", "method", "status", "paid_at")
	list_filter = ("status", "method")


@admin.register(ReservationStatusLog)
class ReservationStatusLogAdmin(admin.ModelAdmin):
	list_display = ("reservation", "previous_status", "new_status", "changed_at")
