from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndexView.as_view(), name="index"),
    path("reportes/", views.ReportsView.as_view(), name="reports"),
    path(
        "api/reservations-by-month/",
        views.reservations_by_month_api,
        name="api_reservations_by_month",
    ),
    path(
        "api/revenue-by-month/",
        views.revenue_by_month_api,
        name="api_revenue_by_month",
    ),
    path("api/top-rooms/", views.top_rooms_api, name="api_top_rooms"),
    path(
        "api/reservations-by-status/",
        views.reservations_by_status_api,
        name="api_reservations_by_status",
    ),
    path(
        "api/occupancy-by-type/",
        views.occupancy_by_room_type_api,
        name="api_occupancy_by_type",
    ),
    path(
        "reportes/reservas/pdf/",
        views.export_reservations_pdf,
        name="reservations_pdf",
    ),
    path(
        "reportes/reservas/excel/",
        views.export_reservations_excel,
        name="reservations_excel",
    ),
    path(
        "reportes/ingresos/pdf/",
        views.export_revenue_pdf,
        name="revenue_pdf",
    ),
    path(
        "reportes/ingresos/excel/",
        views.export_revenue_excel,
        name="revenue_excel",
    ),
    path(
        "reportes/ocupacion/pdf/",
        views.export_occupancy_pdf,
        name="occupancy_pdf",
    ),
]
