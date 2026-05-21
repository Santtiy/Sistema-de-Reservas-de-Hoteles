from io import BytesIO
import base64

import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Payment, Reservation, ReservationStatusLog


def generate_qr_code(text: str) -> bytes:
    img = qrcode.make(text)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_base64(text: str) -> str:
    png_bytes = generate_qr_code(text)
    return base64.b64encode(png_bytes).decode("ascii")


def send_confirmation_email(reservation: Reservation) -> None:
    if not reservation.guest.email:
        return
    qr_png = generate_qr_code(reservation.confirmation_code)
    qr_base64 = base64.b64encode(qr_png).decode("ascii")
    subject = f"Reserva confirmada {reservation.confirmation_code}"
    context = {"reservation": reservation, "qr_base64": qr_base64}
    html_content = render_to_string(
        "reservations/emails/reservation_confirmed.html", context
    )
    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[reservation.guest.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.attach("reserva_qr.png", qr_png, "image/png")
    msg.send(fail_silently=True)


def send_cancellation_email(reservation: Reservation) -> None:
    if not reservation.guest.email:
        return
    subject = f"Reserva cancelada {reservation.confirmation_code}"
    context = {"reservation": reservation}
    html_content = render_to_string(
        "reservations/emails/reservation_cancelled.html", context
    )
    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[reservation.guest.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)


def create_reservation_with_payment(
    user,
    room,
    check_in,
    check_out,
    guests,
    notes,
    payment_data,
) -> Reservation:
    with transaction.atomic():
        reservation = Reservation(
            guest=user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            guests_count=guests,
            notes=notes or "",
            status=Reservation.Status.PENDING,
        )
        reservation.full_clean()
        reservation.save()

        payment = Payment.objects.create(
            reservation=reservation,
            amount=reservation.total_price,
            method=Payment.Method.CARD,
            status=Payment.Status.COMPLETED,
            paid_at=timezone.now(),
            card_last4=payment_data.get("card_last4", ""),
        )
        previous = reservation.status
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        ReservationStatusLog.objects.create(
            reservation=reservation,
            previous_status=previous,
            new_status=Reservation.Status.CONFIRMED,
            changed_by=user,
            notes="Pago simulado confirmado.",
        )
        send_confirmation_email(reservation)
        return reservation


def cancel_reservation(reservation: Reservation, reason: str, user) -> Reservation:
    if not reservation.can_be_cancelled():
        raise ValueError("Reservation cannot be cancelled")
    previous = reservation.status
    reservation.status = Reservation.Status.CANCELLED
    reservation.save(update_fields=["status", "updated_at"])
    ReservationStatusLog.objects.create(
        reservation=reservation,
        previous_status=previous,
        new_status=Reservation.Status.CANCELLED,
        changed_by=user,
        notes=reason or "Cancelada por el usuario.",
    )
    send_cancellation_email(reservation)
    return reservation
