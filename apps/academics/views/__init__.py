# apps/accounts/urls/__init__.py
from django.urls import path, include

urlpatterns = [
    path('students/', include('apps.accounts.urls.student_urls')),
    # Add other account-related URLs here
]