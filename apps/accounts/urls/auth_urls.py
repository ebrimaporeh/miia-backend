# apps/accounts/urls/auth_urls.py
from django.urls import path
from django_rest_passwordreset.views import (
    reset_password_request_token,
    reset_password_confirm,
    reset_password_validate_token
)
from apps.accounts.views.auth import (
    LoginView,
    RegisterView,
    LogoutView,
    ChangePasswordView,
    ProfileView,
    UpdateProfileView,
    ForgotPasswordView,
    CheckAuthView,
    VerifyEmailView,
    ResendVerificationEmailView
)

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='auth_login'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('check/', CheckAuthView.as_view(), name='auth_check'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Password Management
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='auth_forgot_password'),
    
    # Password Reset (using django-rest-passwordreset)
    path('password-reset/', reset_password_request_token, name='reset-password-request'),
    path('password-reset/validate/', reset_password_validate_token, name='reset-password-validate'),
    path('password-reset/confirm/', reset_password_confirm, name='reset-password-confirm'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='auth_profile_update'),
]