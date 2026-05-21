from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    # Público
    path("", views.RoomListView.as_view(), name="list"),
    path("<int:pk>/", views.RoomDetailView.as_view(), name="detail"),

    # Admin habitaciones
    path("admin/", views.RoomAdminListView.as_view(), name="admin_list"),
    path("admin/crear/", views.RoomCreateView.as_view(), name="create"),
    path("admin/<int:pk>/editar/", views.RoomUpdateView.as_view(), name="edit"),
    path("admin/<int:pk>/eliminar/", views.RoomDeleteView.as_view(), name="delete"),
    path("admin/<int:pk>/imagenes/", views.RoomImageManageView.as_view(), name="images"),

    # Tipos
    path("tipos/", views.RoomTypeListView.as_view(), name="type_list"),
    path("tipos/crear/", views.RoomTypeCreateView.as_view(), name="type_create"),
    path("tipos/<int:pk>/editar/", views.RoomTypeUpdateView.as_view(), name="type_edit"),
    path("tipos/<int:pk>/eliminar/", views.RoomTypeDeleteView.as_view(), name="type_delete"),

    # Amenities
    path("amenities/", views.AmenityListView.as_view(), name="amenity_list"),
    path("amenities/crear/", views.AmenityCreateView.as_view(), name="amenity_create"),
    path("amenities/<int:pk>/editar/", views.AmenityUpdateView.as_view(), name="amenity_edit"),
    path("amenities/<int:pk>/eliminar/", views.AmenityDeleteView.as_view(), name="amenity_delete"),
]
