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


def send_enrollment_confirmation_email(parent_user, student_user, student_profile, student_password, parent_password=None):
    """
    Send enrollment confirmation email to parent.
    If parent_password is provided (new parent), include credentials.
    If parent_password is None (existing parent), don't include credentials.
    """
    subject = f"Enrollment Confirmation - {student_user.get_full_name()} - {settings.SITE_NAME}"
    
    context = {
        'site_name': settings.SITE_NAME,
        'support_email': settings.SUPPORT_EMAIL,
        'login_url': f"{settings.FRONTEND_URL}/login",
        'parent_name': parent_user.get_full_name(),
        'parent_email': parent_user.email,
        'student_name': student_user.get_full_name(),
        'student_email': student_user.email,
        'student_id': student_profile.student_id,
        'student_password': student_password,
        'enrollment_date': student_profile.enrollment_date.strftime('%B %d, %Y') if student_profile.enrollment_date else 'N/A',
        'department': student_profile.department or 'Not specified',
    }
    
    # Choose template based on whether this is a new parent or existing parent
    if parent_password:
        # New parent - send full credentials
        context['parent_password'] = parent_password
        html_message = render_to_string('emails/enrollment_confirmation.html', context)
    else:
        # Existing parent - send without password
        html_message = render_to_string('emails/enrollment_parent_existing.html', context)
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send enrollment email: {e}")
        return False



def send_batch_enrollment_summary(parent_user, successful_count, failed_count, 
                                   successful_students, failed_students):
    """
    Send a summary email after batch enrollment
    """
    subject = f"Batch Enrollment Summary - {successful_count} students enrolled - {settings.SITE_NAME}"
    
    context = {
        'site_name': settings.SITE_NAME,
        'support_email': settings.SUPPORT_EMAIL,
        'login_url': f"{settings.FRONTEND_URL}/login",
        'parent_name': parent_user.get_full_name(),
        'successful_count': successful_count,
        'failed_count': failed_count,
        'total_count': successful_count + failed_count,
        'successful_students': successful_students,
        'failed_students': failed_students,
    }
    
    html_message = render_to_string('emails/batch_enrollment_summary.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send batch enrollment summary: {e}")
        return False

def send_student_enrollment_email(student_user, student_password, student_profile):
    """
    Send enrollment confirmation email directly to the student.
    """
    subject = f"Welcome to {settings.SITE_NAME}, {student_user.get_full_name()}!"
    
    context = {
        'site_name': settings.SITE_NAME,
        'support_email': settings.SUPPORT_EMAIL,
        'login_url': f"{settings.FRONTEND_URL}/login",
        'student_name': student_user.get_full_name(),
        'student_email': student_user.email,
        'student_password': student_password,
        'student_id': student_profile.student_id,
    }
    
    html_message = render_to_string('emails/student_enrollment_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send student enrollment email: {e}")
        return False