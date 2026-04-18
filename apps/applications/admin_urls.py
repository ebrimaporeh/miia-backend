# apps/applications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.applications.views import AdminApplicationViewSet

# Only applicant endpoints here
applicant_router = DefaultRouter()
applicant_router.register(r'', AdminApplicationViewSet, basename='application')

urlpatterns = [
    # Applicant endpoints: /api/applications/
    path('', include(applicant_router.urls)),
]