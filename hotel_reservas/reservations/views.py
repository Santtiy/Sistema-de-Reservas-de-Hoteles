from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView

from accounts.decorators import cliente_required, role_required
from rooms.models import Room

from .forms import (
    AdminReservationForm,
    PaymentSimulationForm,
    ReservationCancelForm,
    ReservationFilterForm,
    ReservationForm,
)
from .models import Payment, Reservation, ReservationStatusLog
from .services import (
    cancel_reservation,
    create_reservation_with_payment,
    generate_qr_base64,
)


@method_decorator(cliente_required, name="dispatch")
class ReservationCreateView(View):
    template_name = "reservations/reservation_create.html"

    def _get_params(self, request):
        source = request.POST if request.method == "POST" else request.GET
        room_id = source.get("room")
        check_in = parse_date(source.get("check_in", ""))
        check_out = parse_date(source.get("check_out", ""))
        return room_id, check_in, check_out

    def get(self, request):
        room_id, check_in, check_out = self._get_params(request)
        if not room_id or not check_in or not check_out:
            messages.error(request, "Selecciona una habitacion y fechas validas.")
            return redirect("rooms:list")
        room = get_object_or_404(Room, pk=room_id)
        reservation_form = ReservationForm(initial={"guests_count": 1})
        payment_form = PaymentSimulationForm()
        context = {
            "room": room,
            "check_in": check_in,
            "check_out": check_out,
            "nights": (check_out - check_in).days,
            "total": room.price_for(check_in, check_out),
            "reservation_form": reservation_form,
            "payment_form": payment_form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        room_id, check_in, check_out = self._get_params(request)
        if not room_id or not check_in or not check_out:
            messages.error(request, "Selecciona una habitacion y fechas validas.")
            return redirect("rooms:list")
        room = get_object_or_404(Room, pk=room_id)
        reservation_form = ReservationForm(request.POST)
        payment_form = PaymentSimulationForm(request.POST)
        reservation_form.instance.room = room
        reservation_form.instance.check_in = check_in
        reservation_form.instance.check_out = check_out
        reservation_form.instance.guest = request.user

        if reservation_form.is_valid() and payment_form.is_valid():
            try:
                reservation = create_reservation_with_payment(
                    user=request.user,
                    room=room,
                    check_in=check_in,
                    check_out=check_out,
                    guests=reservation_form.cleaned_data["guests_count"],
                    notes=reservation_form.cleaned_data.get("notes"),
                    payment_data=payment_form.cleaned_data,
                )
                messages.success(request, "Reserva confirmada.")
                return redirect("reservations:detail", pk=reservation.pk)
            except (ValidationError, ValueError) as exc:
                reservation_form.add_error(None, exc)

        context = {
            "room": room,
            "check_in": check_in,
            "check_out": check_out,
            "nights": (check_out - check_in).days,
            "total": room.price_for(check_in, check_out),
            "reservation_form": reservation_form,
            "payment_form": payment_form,
        }
        return render(request, self.template_name, context)


@method_decorator(cliente_required, name="dispatch")
class ReservationListView(ListView):
    model = Reservation
    paginate_by = 10
    template_name = "reservations/reservation_list.html"

    def get_queryset(self):
        return (
            Reservation.objects.filter(guest=self.request.user)
            .select_related("room", "room__room_type")
        )


@method_decorator(cliente_required, name="dispatch")
class ReservationDetailView(DetailView):
    model = Reservation
    template_name = "reservations/reservation_detail.html"

    def get_queryset(self):
        user = self.request.user
        if user.role in ["ADMIN", "RECEPCIONISTA"] or user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(guest=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = self.object
        context["qr_base64"] = generate_qr_base64(reservation.confirmation_code)
        return context


@method_decorator(cliente_required, name="dispatch")
class ReservationCancelView(View):
    template_name = "reservations/reservation_cancel.html"

    def get(self, request, pk):
        reservation = get_object_or_404(
            Reservation, pk=pk, guest=request.user
        )
        form = ReservationCancelForm()
        return render(
            request, self.template_name, {"reservation": reservation, "form": form}
        )

    def post(self, request, pk):
        reservation = get_object_or_404(
            Reservation, pk=pk, guest=request.user
        )
        form = ReservationCancelForm(request.POST)
        if form.is_valid():
            try:
                cancel_reservation(
                    reservation=reservation,
                    reason=form.cleaned_data["reason"],
                    user=request.user,
                )
                messages.success(request, "Reserva cancelada.")
                return redirect("reservations:detail", pk=reservation.pk)
            except ValueError:
                messages.error(request, "No es posible cancelar esta reserva.")
        return render(
            request, self.template_name, {"reservation": reservation, "form": form}
        )


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class AdminReservationListView(ListView):
    model = Reservation
    paginate_by = 20
    template_name = "reservations/admin_list.html"

    def get_queryset(self):
        qs = Reservation.objects.select_related("guest", "room", "room__room_type")
        form = ReservationFilterForm(self.request.GET or None)
        if form.is_valid():
            status = form.cleaned_data.get("status")
            date_from = form.cleaned_data.get("fecha_desde")
            date_to = form.cleaned_data.get("fecha_hasta")
            room = form.cleaned_data.get("room")
            guest_query = form.cleaned_data.get("guest_query")

            if status:
                qs = qs.filter(status=status)
            if date_from:
                qs = qs.filter(check_in__gte=date_from)
            if date_to:
                qs = qs.filter(check_out__lte=date_to)
            if room:
                qs = qs.filter(room=room)
            if guest_query:
                qs = qs.filter(
                    Q(guest__first_name__icontains=guest_query)
                    | Q(guest__last_name__icontains=guest_query)
                    | Q(guest__username__icontains=guest_query)
                    | Q(guest__email__icontains=guest_query)
                )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = ReservationFilterForm(self.request.GET or None)
        return context


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class AdminReservationDetailView(DetailView):
    model = Reservation
    template_name = "reservations/admin_detail.html"

    def get_queryset(self):
        return (
            Reservation.objects.select_related(
                "guest", "room", "room__room_type", "payment"
            ).prefetch_related("status_logs")
        )


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class AdminReservationUpdateView(UpdateView):
    model = Reservation
    form_class = AdminReservationForm
    template_name = "reservations/admin_form.html"

    def form_valid(self, form):
        previous_status = self.get_object().status
        response = super().form_valid(form)
        new_status = self.object.status
        if previous_status != new_status:
            ReservationStatusLog.objects.create(
                reservation=self.object,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=self.request.user,
                notes="Actualizado desde administracion.",
            )
        return response

    def get_success_url(self):
        return redirect("reservations:admin_detail", pk=self.object.pk).url


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class RefundView(View):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        payment = getattr(reservation, "payment", None)
        if not payment:
            messages.error(request, "No hay pago registrado.")
            return redirect("reservations:admin_detail", pk=reservation.pk)
        payment.status = Payment.Status.REFUNDED
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])
        ReservationStatusLog.objects.create(
            reservation=reservation,
            previous_status=reservation.status,
            new_status=reservation.status,
            changed_by=request.user,
            notes="Reembolso registrado.",
        )
        messages.success(request, "Pago reembolsado.")
        return redirect("reservations:admin_detail", pk=reservation.pk)
