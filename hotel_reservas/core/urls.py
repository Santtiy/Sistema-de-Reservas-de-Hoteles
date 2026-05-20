from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("core.home_urls")),
    path("accounts/", include("accounts.urls")),
    path("rooms/", include("rooms.urls")),
    path("reservations/", include("reservations.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
