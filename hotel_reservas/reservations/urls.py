from django.urls import path

from .views import (
    AdminReservationDetailView,
    AdminReservationListView,
    AdminReservationUpdateView,
    RefundView,
    ReservationCancelView,
    ReservationCreateView,
    ReservationDetailView,
    ReservationListView,
)

app_name = "reservations"

urlpatterns = [
    path("", ReservationListView.as_view(), name="list"),
    path("crear/", ReservationCreateView.as_view(), name="create"),
    path("<int:pk>/", ReservationDetailView.as_view(), name="detail"),
    path("<int:pk>/cancelar/", ReservationCancelView.as_view(), name="cancel"),
    path("admin/", AdminReservationListView.as_view(), name="admin_list"),
    path("admin/<int:pk>/", AdminReservationDetailView.as_view(), name="admin_detail"),
    path("admin/<int:pk>/editar/", AdminReservationUpdateView.as_view(), name="admin_edit"),
    path("admin/<int:pk>/reembolsar/", RefundView.as_view(), name="refund"),
]
