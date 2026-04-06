# apps/applications/utils.py
import logging
import secrets
import string
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Parent, Student
from apps.accounts.utils.student_utils import generate_student_id, generate_student_email

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def send_verification_email(user, verification_url):
    """Send email verification email to user (synchronous)"""
    try:
        subject = f"Verify your email address - {settings.SITE_NAME}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
            'expiry_hours': 24,
        }
        
        html_message = render_to_string('emails/verify_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_welcome_email(user, password=None, email=None):
    """Send welcome email to newly registered user (synchronous)"""
    try:
        recipient_email = email or user.email
        
        subject = f"Welcome to {settings.SITE_NAME}!"
        
        context = {
            'user': user,
            'password': password,
            'site_name': settings.SITE_NAME,
            'login_url': f"{settings.FRONTEND_URL}/login",
            'support_email': settings.SUPPORT_EMAIL,
        }
        
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False


def send_application_approved_email(parent_user, parent_name, children_names, password=None):
    """Send email to parent when application is approved (synchronous)"""
    try:
        subject = f"Application Approved - Welcome to {settings.SITE_NAME}!"
        
        context = {
            'user': parent_user,
            'parent_name': parent_name,
            'children_names': children_names,
            'password': password,
            'site_name': settings.SITE_NAME,
            'login_url': f"{settings.FRONTEND_URL}/login",
            'support_email': settings.SUPPORT_EMAIL,
        }
        
        html_message = render_to_string('emails/application_approved.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Application approved email sent to {parent_user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send approval email to {parent_user.email}: {e}")
        return False


def send_application_rejected_email(applicant_email, applicant_name, rejection_reason):
    """Send rejection email to applicant (synchronous)"""
    try:
        subject = f"Application Update - {settings.SITE_NAME}"
        
        context = {
            'name': applicant_name,
            'rejection_reason': rejection_reason,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
        }
        
        html_message = render_to_string('emails/application_rejected.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[applicant_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Rejection email sent to {applicant_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send rejection email to {applicant_email}: {e}")
        return False


def send_password_reset_email(user, reset_link):
    """Send password reset email to user (synchronous)"""
    try:
        subject = f"Password Reset Request - {settings.SITE_NAME}"
        
        context = {
            'user': user,
            'reset_link': reset_link,
            'site_name': settings.SITE_NAME,
            'support_email': settings.SUPPORT_EMAIL,
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False


def create_parent_and_students_from_application(application):
    """Create Parent and Student records from approved application (synchronous)"""
    from apps.applications.models import Application
    
    try:
        # Check if already processed
        if application.parent:
            logger.info(f"Application {application.id} already processed")
            return {'status': 'already_processed', 'application_id': str(application.id)}
        
        with transaction.atomic():
            # Get applicant parent data
            applicant_parent = application.applicant_parent
            applicant_user = application.applicant
            
            parent_email = applicant_parent.email
            applicant_email = applicant_user.email
            
            parent_user = None
            generated_password = None
            
            # Determine if we need to create a new parent or convert the applicant
            if parent_email == applicant_email:
                # Same email - convert applicant to parent
                logger.info(f"Converting applicant {applicant_email} to parent role")
                
                # Update applicant user to parent
                applicant_user.role = 'parent'
                applicant_user.first_name = applicant_parent.first_name
                applicant_user.last_name = applicant_parent.last_name
                applicant_user.phone = applicant_parent.phone
                applicant_user.is_active = True
                applicant_user.save()
                
                parent_user = applicant_user
                
            else:
                # Different email - create new parent account
                logger.info(f"Creating new parent account with email {parent_email}")
                
                # Check if parent user already exists
                existing_parent = User.objects.filter(email=parent_email).first()
                
                if existing_parent:
                    # Parent user already exists, use it
                    parent_user = existing_parent
                    logger.info(f"Parent user already exists: {parent_email}")
                else:
                    # Create new parent user
                    generated_password = generate_secure_password()
                    username = parent_email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    parent_user = User.objects.create_user(
                        username=username,
                        email=parent_email,
                        password=generated_password,
                        first_name=applicant_parent.first_name,
                        last_name=applicant_parent.last_name,
                        role='parent',
                        is_active=True
                    )
                    logger.info(f"Created new parent user: {parent_email}")
            
            # Create or get Parent profile
            parent, created = Parent.objects.get_or_create(
                user=parent_user,
                defaults={
                    'relationship': applicant_parent.relationship,
                    'occupation': applicant_parent.occupation,
                    'phone': applicant_parent.phone,
                    'alternate_phone': applicant_parent.alternate_phone,
                    'address': applicant_parent.address,
                }
            )
            
            if not created:
                # Update existing parent profile
                parent.relationship = applicant_parent.relationship
                parent.occupation = applicant_parent.occupation
                parent.phone = applicant_parent.phone
                parent.alternate_phone = applicant_parent.alternate_phone
                parent.address = applicant_parent.address
                parent.save()
                logger.info(f"Updated existing parent profile for {parent_user.email}")
            
            # Create Student records for each child
            created_students = []
            children_names = []
            
            for child_data in application.applicant_children.all():
                # Generate student email
                student_email = generate_student_email(child_data.first_name, child_data.last_name)
                children_names.append(f"{child_data.first_name} {child_data.last_name}")
                
                # Check if student already exists
                existing_student_user = User.objects.filter(email=student_email).first()
                
                if existing_student_user:
                    # Update existing user
                    student_user = existing_student_user
                    student_user.first_name = child_data.first_name
                    student_user.last_name = child_data.last_name
                    student_user.role = 'student'
                    student_user.is_active = True
                    student_user.save()
                    logger.info(f"Updated existing student user: {student_email}")
                else:
                    # Create username from name
                    username = f"{child_data.first_name.lower()}.{child_data.last_name.lower()}"
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    # Create new user for student
                    student_user = User.objects.create_user(
                        username=username,
                        email=student_email,
                        password=generate_secure_password(),
                        first_name=child_data.first_name,
                        last_name=child_data.last_name,
                        role='student',
                        is_active=True
                    )
                    logger.info(f"Created new student user: {student_email}")
                
                # Create or update Student profile
                student, student_created = Student.objects.get_or_create(
                    user=student_user,
                    defaults={
                        'student_id': generate_student_id(),
                        'date_of_birth': child_data.date_of_birth,
                        'gender': child_data.gender,
                        'enrollment_date': timezone.now().date(),
                        'status': 'active',
                        'has_allergies': child_data.has_allergies,
                        'allergy_details': child_data.allergy_details,
                        'medical_conditions': child_data.medical_conditions,
                        'phone': child_data.phone,
                        'address': child_data.address or applicant_parent.address,
                        'guardian_name': applicant_parent.full_name,
                        'guardian_phone': applicant_parent.phone,
                        'guardian_email': parent_user.email,
                        'guardian_relationship': applicant_parent.relationship,
                    }
                )
                
                if not student_created:
                    # Update existing student profile
                    student.date_of_birth = child_data.date_of_birth
                    student.gender = child_data.gender
                    student.has_allergies = child_data.has_allergies
                    student.allergy_details = child_data.allergy_details
                    student.medical_conditions = child_data.medical_conditions
                    student.phone = child_data.phone
                    student.address = child_data.address or applicant_parent.address
                    student.guardian_name = applicant_parent.full_name
                    student.guardian_phone = applicant_parent.phone
                    student.guardian_email = parent_user.email
                    student.guardian_relationship = applicant_parent.relationship
                    student.save()
                    logger.info(f"Updated existing student profile for {student_email}")
                
                # Link to parent
                parent.children.add(student)
                created_students.append(student)
            
            # Update application
            application.parent = parent
            application.save()
            
            logger.info(f"Parent and {len(created_students)} students created/updated from application {application.id}")
            
            # Send application approved email (synchronous)
            send_application_approved_email(
                parent_user,
                parent_user.get_full_name(),
                children_names,
                generated_password
            )
            
            return {
                'status': 'success',
                'application_id': str(application.id),
                'parent_user_id': str(parent_user.id),
                'parent_email': parent_user.email,
                'student_ids': [str(s.user.id) for s in created_students],
                'password_generated': generated_password is not None,
                'email_sent': True
            }
            
    except Exception as e:
        logger.error(f"Failed to create parent/students from application {application.id}: {e}", exc_info=True)
        raise