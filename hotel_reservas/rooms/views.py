from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from accounts.decorators import role_required

from .forms import (
    AmenityForm,
    RoomForm,
    RoomImageFormSet,
    RoomSearchForm,
    RoomTypeForm,
)
from .models import Amenity, Room, RoomType


staff_required = method_decorator(
    role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch"
)


def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# ===== PÚBLICO =====

class RoomListView(ListView):
    """Catálogo público de habitaciones con filtros."""

    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"
    paginate_by = 9

    def get_queryset(self):
        qs = Room.objects.select_related("room_type").prefetch_related("images", "amenities")
        g = self.request.GET
        room_type = g.get("room_type")
        capacity_min = g.get("capacity_min")
        price_max = g.get("price_max")
        check_in = _parse_date(g.get("check_in"))
        check_out = _parse_date(g.get("check_out"))

        if room_type:
            qs = qs.filter(room_type_id=room_type)
        if capacity_min:
            try:
                qs = qs.filter(room_type__capacity__gte=int(capacity_min))
            except ValueError:
                pass
        if price_max:
            try:
                qs = qs.filter(room_type__base_price__lte=price_max)
            except (TypeError, ValueError):
                pass
        if check_in and check_out and check_out > check_in:
            available_ids = [
                r.pk for r in qs if r.is_available_between(check_in, check_out)
            ]
            qs = qs.filter(pk__in=available_ids)
        else:
            qs = qs.filter(status=Room.Status.AVAILABLE)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = RoomSearchForm(self.request.GET or None)
        ctx["check_in"] = self.request.GET.get("check_in", "")
        ctx["check_out"] = self.request.GET.get("check_out", "")
        return ctx


class RoomDetailView(DetailView):
    """Detalle público con galería, amenities y selector de fechas."""

    model = Room
    template_name = "rooms/room_detail.html"
    context_object_name = "room"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        room = self.object
        g = self.request.GET
        ctx["images"] = room.images.all()
        ctx["search_form"] = RoomSearchForm(g or None)
        check_in = _parse_date(g.get("check_in"))
        check_out = _parse_date(g.get("check_out"))
        if check_in and check_out and check_out > check_in:
            ctx["check_in"] = check_in
            ctx["check_out"] = check_out
            ctx["nights"] = (check_out - check_in).days
            ctx["total_price"] = room.price_for(check_in, check_out)
            ctx["is_available"] = room.is_available_between(check_in, check_out)
        return ctx


# ===== ADMIN ROOMS =====

@staff_required
class RoomAdminListView(ListView):
    model = Room
    template_name = "rooms/room_admin_list.html"
    context_object_name = "rooms"
    paginate_by = 20

    def get_queryset(self):
        return (
            Room.objects.select_related("room_type")
            .prefetch_related("images")
            .order_by("number")
        )


@staff_required
class RoomCreateView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("rooms:admin_list")

    def form_valid(self, form):
        messages.success(self.request, "Habitación creada correctamente.")
        return super().form_valid(form)


@staff_required
class RoomUpdateView(UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("rooms:admin_list")

    def form_valid(self, form):
        messages.success(self.request, "Habitación actualizada.")
        return super().form_valid(form)


@staff_required
class RoomDeleteView(DeleteView):
    model = Room
    template_name = "rooms/room_confirm_delete.html"
    success_url = reverse_lazy("rooms:admin_list")

    def form_valid(self, form):
        messages.success(self.request, "Habitación eliminada.")
        return super().form_valid(form)


@method_decorator(role_required(["ADMIN", "RECEPCIONISTA"]), name="dispatch")
class RoomImageManageView(LoginRequiredMixin, View):
    """Gestiona imágenes (URLs) de una habitación con un inline formset."""

    template_name = "rooms/room_images.html"

    def get(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        formset = RoomImageFormSet(instance=room)
        return render(request, self.template_name, {"room": room, "formset": formset})

    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        formset = RoomImageFormSet(request.POST, instance=room)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Imágenes actualizadas.")
            return redirect("rooms:images", pk=room.pk)
        messages.error(request, "Revisa los errores del formulario.")
        return render(request, self.template_name, {"room": room, "formset": formset})


# ===== ADMIN ROOM TYPES =====

@staff_required
class RoomTypeListView(ListView):
    model = RoomType
    template_name = "rooms/type_list.html"
    context_object_name = "types"


@staff_required
class RoomTypeCreateView(CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = "rooms/type_form.html"
    success_url = reverse_lazy("rooms:type_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo creado.")
        return super().form_valid(form)


@staff_required
class RoomTypeUpdateView(UpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = "rooms/type_form.html"
    success_url = reverse_lazy("rooms:type_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo actualizado.")
        return super().form_valid(form)


@staff_required
class RoomTypeDeleteView(DeleteView):
    model = RoomType
    template_name = "rooms/type_confirm_delete.html"
    success_url = reverse_lazy("rooms:type_list")

    def form_valid(self, form):
        messages.success(self.request, "Tipo eliminado.")
        return super().form_valid(form)


# ===== ADMIN AMENITIES =====

@staff_required
class AmenityListView(ListView):
    model = Amenity
    template_name = "rooms/amenity_list.html"
    context_object_name = "amenities"


@staff_required
class AmenityCreateView(CreateView):
    model = Amenity
    form_class = AmenityForm
    template_name = "rooms/amenity_form.html"
    success_url = reverse_lazy("rooms:amenity_list")

    def form_valid(self, form):
        messages.success(self.request, "Amenity creada.")
        return super().form_valid(form)


@staff_required
class AmenityUpdateView(UpdateView):
    model = Amenity
    form_class = AmenityForm
    template_name = "rooms/amenity_form.html"
    success_url = reverse_lazy("rooms:amenity_list")

    def form_valid(self, form):
        messages.success(self.request, "Amenity actualizada.")
        return super().form_valid(form)


@staff_required
class AmenityDeleteView(DeleteView):
    model = Amenity
    template_name = "rooms/amenity_confirm_delete.html"
    success_url = reverse_lazy("rooms:amenity_list")

    def form_valid(self, form):
        messages.success(self.request, "Amenity eliminada.")
        return super().form_valid(form)
