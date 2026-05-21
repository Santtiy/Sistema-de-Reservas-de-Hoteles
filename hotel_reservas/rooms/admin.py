from django.contrib import admin

from .models import Amenity, Room, RoomImage, RoomType


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "base_price", "capacity")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ("name",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "room_type", "floor", "status")
    list_filter = ("status", "room_type", "floor")
    search_fields = ("number", "room_type__name")
    inlines = [RoomImageInline]
    filter_horizontal = ("amenities",)


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ("room", "caption", "is_main")
    list_filter = ("is_main",)
