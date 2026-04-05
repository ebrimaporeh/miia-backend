from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # API Documentation
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Redis Queue
    path('admin/rq/', include('django_rq.urls')),

    # Authentication endpoints
    path("api/auth/", include("apps.accounts.urls.auth_urls")),
    path('api/accounts/', include('apps.accounts.urls')),
    path("api/academics/", include("apps.academics.urls")),

    # Future modules
    path("api/applications/", include("apps.applications.urls")),
    # path("api/schedule/", include("apps.schedule.urls")),
    # path("api/results/", include("apps.assessment.urls")),
    # path("api/attendance/", include("apps.attendance.urls")),
    # path("api/fees/", include("apps.finance.urls")),
    # path("api/announcements/", include("apps.announcements.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)