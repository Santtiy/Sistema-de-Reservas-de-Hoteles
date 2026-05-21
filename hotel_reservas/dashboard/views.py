from __future__ import annotations

from datetime import date, datetime, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from accounts.decorators import role_required
from reservations.models import Payment, Reservation
from rooms.models import RoomType

from .services import (
    generate_excel_report,
    generate_pdf_report,
    get_kpis,
    get_reservations_queryset,
)


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1)


def _month_range_last_12() -> list[date]:
    today = timezone.localdate()
    start = _add_months(_month_start(today), -11)
    return [_add_months(start, offset) for offset in range(12)]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class DashboardIndexView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kpis"] = get_kpis()
        return context


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class ReportsView(TemplateView):
    template_name = "dashboard/reports.html"


@role_required(["ADMIN", "RECEPCIONISTA"])
def reservations_by_month_api(request):
    months = _month_range_last_12()
    start = months[0]
    end = _add_months(months[-1], 1)

    qs = (
        Reservation.objects.filter(check_in__gte=start, check_in__lt=end)
        .annotate(month=TruncMonth("check_in"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    totals = {}
    for row in qs:
        month_value = row["month"]
        if hasattr(month_value, "date"):
            month_value = month_value.date()
        totals[month_value] = row["total"]

    labels = [m.strftime("%m/%Y") for m in months]
    data = [totals.get(m, 0) for m in months]
    return JsonResponse({"labels": labels, "data": data})


@role_required(["ADMIN", "RECEPCIONISTA"])
def revenue_by_month_api(request):
    months = _month_range_last_12()
    start = months[0]
    end = _add_months(months[-1], 1)

    qs = (
        Payment.objects.filter(status=Payment.Status.COMPLETED, paid_at__isnull=False)
        .filter(paid_at__date__gte=start, paid_at__date__lt=end)
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    totals = {}
    for row in qs:
        month_value = row["month"]
        if hasattr(month_value, "date"):
            month_value = month_value.date()
        totals[month_value] = float(row["total"] or 0)

    labels = [m.strftime("%m/%Y") for m in months]
    data = [totals.get(m, 0) for m in months]
    return JsonResponse({"labels": labels, "data": data})


@role_required(["ADMIN", "RECEPCIONISTA"])
def top_rooms_api(request):
    qs = (
        Reservation.objects.exclude(status=Reservation.Status.CANCELLED)
        .values("room__number", "room__room_type__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    labels = [f"{row['room__number']} - {row['room__room_type__name']}" for row in qs]
    data = [row["total"] for row in qs]
    return JsonResponse({"labels": labels, "data": data})


@role_required(["ADMIN", "RECEPCIONISTA"])
def reservations_by_status_api(request):
    qs = Reservation.objects.values("status").annotate(total=Count("id"))
    totals = {row["status"]: row["total"] for row in qs}

    labels = [label for _, label in Reservation.Status.choices]
    data = [totals.get(key, 0) for key, _ in Reservation.Status.choices]
    return JsonResponse({"labels": labels, "data": data})


@role_required(["ADMIN", "RECEPCIONISTA"])
def occupancy_by_room_type_api(request):
    today = timezone.localdate()
    month_start = _month_start(today)
    next_month = _add_months(month_start, 1)
    total_days = (next_month - month_start).days

    labels = []
    data = []

    for room_type in RoomType.objects.all():
        rooms_count = room_type.rooms.count()
        total_room_nights = rooms_count * total_days
        if total_room_nights == 0:
            occupancy = 0
        else:
            reservations = (
                Reservation.objects.filter(room__room_type=room_type)
                .exclude(status=Reservation.Status.CANCELLED)
                .filter(check_in__lt=next_month, check_out__gt=month_start)
            )
            booked_nights = 0
            for reservation in reservations:
                start = max(reservation.check_in, month_start)
                end = min(reservation.check_out, next_month)
                booked_nights += max((end - start).days, 0)
            occupancy = round((booked_nights / total_room_nights) * 100, 2)

        labels.append(room_type.name)
        data.append(occupancy)

    return JsonResponse({"labels": labels, "data": data})


@role_required(["ADMIN", "RECEPCIONISTA"])
def export_reservations_pdf(request):
    filters = {
        "fecha_inicio": _parse_date(request.GET.get("fecha_inicio")),
        "fecha_fin": _parse_date(request.GET.get("fecha_fin")),
        "status": request.GET.get("status") or "ALL",
    }
    qs = get_reservations_queryset(filters)

    headers = [
        "Codigo",
        "Huesped",
        "Habitacion",
        "Check-in",
        "Check-out",
        "Noches",
        "Total",
        "Estado",
    ]
    rows = []
    for reservation in qs:
        guest_name = (
            reservation.guest.get_full_name().strip() or reservation.guest.username
        )
        rows.append(
            [
                reservation.confirmation_code,
                guest_name,
                reservation.room.number,
                reservation.check_in.strftime("%Y-%m-%d"),
                reservation.check_out.strftime("%Y-%m-%d"),
                str(reservation.nights),
                f"{reservation.total_price:.2f}",
                reservation.get_status_display(),
            ]
        )

    total_reservations = qs.count()
    total_revenue = qs.aggregate(total=Sum("total_price"))["total"] or 0
    footer = [
        f"Total de reservas: {total_reservations}",
        f"Ingresos estimados: {total_revenue:.2f}",
    ]

    title_parts = ["Reporte de reservas"]
    if filters["fecha_inicio"] or filters["fecha_fin"]:
        title_parts.append(
            f"{filters['fecha_inicio'] or '...'} a {filters['fecha_fin'] or '...'}"
        )
    title = " - ".join(title_parts)

    return generate_pdf_report(
        title=title,
        headers=headers,
        rows=rows,
        filename="reporte_reservas.pdf",
        footer_summary=footer,
    )


@role_required(["ADMIN", "RECEPCIONISTA"])
def export_reservations_excel(request):
    filters = {
        "fecha_inicio": _parse_date(request.GET.get("fecha_inicio")),
        "fecha_fin": _parse_date(request.GET.get("fecha_fin")),
        "status": request.GET.get("status") or "ALL",
    }
    qs = get_reservations_queryset(filters)

    headers = [
        "Codigo",
        "Huesped",
        "Habitacion",
        "Check-in",
        "Check-out",
        "Noches",
        "Total",
        "Estado",
    ]
    rows = []
    for reservation in qs:
        guest_name = (
            reservation.guest.get_full_name().strip() or reservation.guest.username
        )
        rows.append(
            [
                reservation.confirmation_code,
                guest_name,
                reservation.room.number,
                reservation.check_in.strftime("%Y-%m-%d"),
                reservation.check_out.strftime("%Y-%m-%d"),
                reservation.nights,
                float(reservation.total_price),
                reservation.get_status_display(),
            ]
        )

    return generate_excel_report(
        title="Reporte de reservas",
        headers=headers,
        rows=rows,
        filename="reporte_reservas.xlsx",
    )


def _revenue_by_month(start: date | None, end: date | None):
    qs = Payment.objects.filter(status=Payment.Status.COMPLETED, paid_at__isnull=False)
    if start:
        qs = qs.filter(paid_at__date__gte=start)
    if end:
        qs = qs.filter(paid_at__date__lte=end)

    return (
        qs.annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )


@role_required(["ADMIN", "RECEPCIONISTA"])
def export_revenue_pdf(request):
    start = _parse_date(request.GET.get("fecha_inicio"))
    end = _parse_date(request.GET.get("fecha_fin"))
    qs = _revenue_by_month(start, end)

    headers = ["Mes", "Ingresos"]
    rows = []
    total_revenue = 0
    for row in qs:
        month_value = row["month"]
        if hasattr(month_value, "date"):
            month_value = month_value.date()
        label = month_value.strftime("%m/%Y") if month_value else "-"
        amount = float(row["total"] or 0)
        total_revenue += amount
        rows.append([label, f"{amount:.2f}"])

    footer = [f"Total ingresos: {total_revenue:.2f}"]
    title_parts = ["Reporte de ingresos"]
    if start or end:
        title_parts.append(f"{start or '...'} a {end or '...'}")

    return generate_pdf_report(
        title=" - ".join(title_parts),
        headers=headers,
        rows=rows,
        filename="reporte_ingresos.pdf",
        footer_summary=footer,
    )


@role_required(["ADMIN", "RECEPCIONISTA"])
def export_revenue_excel(request):
    start = _parse_date(request.GET.get("fecha_inicio"))
    end = _parse_date(request.GET.get("fecha_fin"))
    qs = _revenue_by_month(start, end)

    headers = ["Mes", "Ingresos"]
    rows = []
    for row in qs:
        month_value = row["month"]
        if hasattr(month_value, "date"):
            month_value = month_value.date()
        label = month_value.strftime("%m/%Y") if month_value else "-"
        rows.append([label, float(row["total"] or 0)])

    return generate_excel_report(
        title="Reporte de ingresos",
        headers=headers,
        rows=rows,
        filename="reporte_ingresos.xlsx",
    )


@role_required(["ADMIN", "RECEPCIONISTA"])
def export_occupancy_pdf(request):
    start = _parse_date(request.GET.get("fecha_inicio"))
    end = _parse_date(request.GET.get("fecha_fin"))
    if not start or not end or end < start:
        today = timezone.localdate()
        start = _month_start(today)
        end = _add_months(start, 1) - timedelta(days=1)

    total_days = (end - start).days + 1
    headers = ["Tipo de habitacion", "Ocupacion (%)"]
    rows = []

    for room_type in RoomType.objects.all():
        rooms_count = room_type.rooms.count()
        total_room_nights = rooms_count * total_days
        if total_room_nights == 0:
            occupancy = 0
        else:
            reservations = (
                Reservation.objects.filter(room__room_type=room_type)
                .exclude(status=Reservation.Status.CANCELLED)
                .filter(check_in__lte=end, check_out__gte=start)
            )
            booked_nights = 0
            for reservation in reservations:
                overlap_start = max(reservation.check_in, start)
                overlap_end = min(reservation.check_out, end + timedelta(days=1))
                booked_nights += max((overlap_end - overlap_start).days, 0)
            occupancy = round((booked_nights / total_room_nights) * 100, 2)

        rows.append([room_type.name, f"{occupancy:.2f}"])

    title = f"Reporte de ocupacion - {start} a {end}"
    return generate_pdf_report(
        title=title,
        headers=headers,
        rows=rows,
        filename="reporte_ocupacion.pdf",
    )
