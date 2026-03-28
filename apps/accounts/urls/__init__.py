from django.urls import path, include

urlpatterns = [
    # Authentication URLs
    path('auth/', include('apps.accounts.urls.auth_urls')),

    # Student management URLs
    path('students/', include('apps.accounts.urls.student_urls')),

    # parent management URLs
    path('parent/', include('apps.accounts.urls.parent_urls')),

    # User management URLs
    path('users/', include('apps.accounts.urls.user_urls')),
]