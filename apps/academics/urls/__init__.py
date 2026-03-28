# apps/academics/urls/__init__.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.academics.views.course_views import (
    CourseViewSet, SubjectViewSet, AcademicYearViewSet, TermViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'subjects', SubjectViewSet)
router.register(r'academic-years', AcademicYearViewSet)
router.register(r'terms', TermViewSet)

urlpatterns = [
    path('', include(router.urls)),
]