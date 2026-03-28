# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from apps.accounts.models import Teacher, Student, Parent, Staff
from apps.applications.models import Application

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
            # Don't create student here - let the student creation flow handle it
            # This prevents duplicate student creation
            pass
        elif instance.role == 'parent':
            Parent.objects.create(
                user=instance,
                relationship="guardian"
            )
            # Create application for parent
            Application.objects.create(
                applicant=instance,
                status='in_progress',
                current_step=1,
                terms_accepted=False,
                privacy_accepted=False
            )
        elif instance.role == 'staff':
            Staff.objects.create(
                user=instance,
                staff_id=f"STF{str(instance.id).replace('-', '')[:8].upper()}",
                department="To be assigned",
                position="To be assigned",
                joining_date=instance.date_joined.date()
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
        try:
            group = Group.objects.get(name=instance.role)
            instance.groups.add(group)
        except Group.DoesNotExist:
            # Group doesn't exist yet, will be created by management command
            pass