"""
URL configuration for etude_huissier project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("comptabilite/", include("comptabilite.urls")),
    path("rh/", include("rh.urls")),
    path("documents/", include("documents.urls")),
    path("agenda/", include("agenda.urls")),
    path("citations/", include("citations.urls")),
    path("", include("gestion.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
