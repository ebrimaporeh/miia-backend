# apps/accounts/urls/user_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views import (
    UserViewSet,
    TeacherViewSet,
    StaffViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'teachers', TeacherViewSet, basename='teacher')
# router.register(r'parents', ParentViewSet, basename='parent')
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('', include(router.urls)),
]