# apps/accounts/email_utils.py
import secrets
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import jwt


def generate_verification_token(user_id):
    """Generate JWT token for email verification"""
    payload = {
        'user_id': str(user_id),
        'type': 'email_verification',
        'exp': timezone.now() + timezone.timedelta(days=1)  
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def verify_email_token(token):
    """Verify email verification token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != 'email_verification':
            return None
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def send_verification_email(user, request):
    """Send email verification link to user"""
    token = generate_verification_token(user.id)
    
    # Store token in user model
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    # Build verification URL
    verification_url = f"{settings.FRONTEND_URL}/verify?token={token}"
    
    # Email subject and content
    subject = f"Verify your email address - {settings.SITE_NAME}"
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': settings.SITE_NAME,
        'support_email': settings.SUPPORT_EMAIL,
        'expiry_hours': 24,
    }
    
    # Render HTML template
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )