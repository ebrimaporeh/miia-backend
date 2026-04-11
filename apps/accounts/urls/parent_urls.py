# apps/accounts/urls/parent_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views.parent_views import (
    ParentsViewSet, 
    ParentProfileViewSet, 
    ParentChildrenViewSet
)

router = DefaultRouter()
# Register at root of /parent/ namespace for admin parent management
router.register(r'', ParentsViewSet, basename='parents')  # /api/accounts/parent/
router.register(r'profile', ParentProfileViewSet, basename='parent-profile')  # /api/accounts/parent/profile/
router.register(r'children', ParentChildrenViewSet, basename='parent-children')  # /api/accounts/parent/children/

urlpatterns = [
    path('', include(router.urls)),
]