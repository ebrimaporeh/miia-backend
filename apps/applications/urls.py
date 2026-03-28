# apps/applications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.applications.views import ApplicationViewSet, AdminApplicationViewSet

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'admin/applications', AdminApplicationViewSet, basename='admin-application')

urlpatterns = [
    path('', include(router.urls)),
]