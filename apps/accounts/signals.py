# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from apps.accounts.models import Teacher, Student, Parent, Staff
from apps.applications.models import Application
from apps.accounts.utils.student_utils import generate_student_id
from django.utils import timezone


User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile based on role when a new user is created"""
    if created:
        if instance.role == 'teacher':
            Teacher.objects.create(
                user=instance,
                employee_id=f"TCH{str(instance.id).replace('-', '')[:8].upper()}",
                qualification="To be updated",
                specialization="To be updated",
                joining_date=instance.date_joined.date()
            )
        elif instance.role == 'student':
            # Create student profile here
            Student.objects.create(
                user=instance,
                student_id=generate_student_id(),  # You'll need to import this
                enrollment_date=timezone.now().date(),
                status='pending'
            )
        elif instance.role == 'parent':
            Parent.objects.create(
                user=instance,
                relationship="guardian"
            )
            # No application for parents - parents are created after approval
        elif instance.role == 'staff':
            Staff.objects.create(
                user=instance,
                staff_id=f"STF{str(instance.id).replace('-', '')[:8].upper()}",
                department="To be assigned",
                position="To be assigned",
                joining_date=instance.date_joined.date()
            )
        elif instance.role == 'applicant':
            # Create application for applicant
            Application.objects.create(
                applicant=instance,
                status='draft',
                current_step=1,
               
            )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when user is saved"""
    if instance.role == 'teacher' and hasattr(instance, 'teacher_profile'):
        instance.teacher_profile.save()
    elif instance.role == 'student' and hasattr(instance, 'student_profile'):
        instance.student_profile.save()
    elif instance.role == 'parent' and hasattr(instance, 'parent_profile'):
        instance.parent_profile.save()
    elif instance.role == 'staff' and hasattr(instance, 'staff_profile'):
        instance.staff_profile.save()

@receiver(post_save, sender=User)
def assign_user_group(sender, instance, created, **kwargs):
    """Assign user to appropriate group based on role"""
    if created:
        group_mapping = {
            'admin': 'admin',
            'teacher': 'teacher',
            'student': 'student',
            'parent': 'parent',
            'staff': 'staff',
            'applicant': 'applicant',
        }
        group_name = group_mapping.get(instance.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                instance.groups.add(group)
            except Group.DoesNotExist:
                # Group doesn't exist yet, will be created by management command
                pass