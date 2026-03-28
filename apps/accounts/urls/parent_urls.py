# apps/accounts/urls/parent_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views.parent_views import ParentProfileViewSet, ParentChildrenViewSet

router = DefaultRouter()
router.register(r'profile', ParentProfileViewSet, basename='parent-profile')
router.register(r'children', ParentChildrenViewSet, basename='parent-children')

urlpatterns = [
    path('', include(router.urls)),
]