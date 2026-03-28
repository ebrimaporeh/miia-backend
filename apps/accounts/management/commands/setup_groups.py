# apps/accounts/management/commands/setup_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction

class Command(BaseCommand):
    help = 'Sets up default groups and permissions based on user types'
    
    def get_permission(self, codename):
        """Get permission by codename"""
        try:
            return Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Permission '{codename}' not found"))
            return None
        except Permission.MultipleObjectsReturned:
            # Handle duplicate permissions
            return Permission.objects.filter(codename=codename).first()
    
    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up groups and permissions...')
        
        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='admin')
        teacher_group, _ = Group.objects.get_or_create(name='teacher')
        student_group, _ = Group.objects.get_or_create(name='student')
        parent_group, _ = Group.objects.get_or_create(name='parent')
        staff_group, _ = Group.objects.get_or_create(name='staff')
        
        # Clear existing permissions
        admin_group.permissions.clear()
        teacher_group.permissions.clear()
        student_group.permissions.clear()
        parent_group.permissions.clear()
        staff_group.permissions.clear()
        
        # Get all permissions
        all_permissions = Permission.objects.all()
        
        # Admin gets all permissions
        admin_group.permissions.set(all_permissions)
        self.stdout.write(f'✓ Admin group: {all_permissions.count()} permissions')
        
        # Teacher permissions
        teacher_perms = [
            # Course permissions
            'course:view', 'course:edit', 'course:enroll',
            # Assignment permissions
            'assignment:view', 'assignment:create', 'assignment:edit', 'assignment:grade',
            # Grade permissions
            'grade:view', 'grade:edit',
            # Schedule permissions
            'schedule:view', 'schedule:attend',
            # Student permissions
            'student:view', 'student:attendance:mark', 'student:progress:view', 'student:progress:edit',
            'student:behavior:view', 'student:behavior:report',
            # Parent permissions
            'parent:view', 'parent:communicate', 'parent:meeting:schedule', 'parent:progress:view',
            # Teacher self permissions
            'teacher:view', 'teacher:schedule:view', 'teacher:leave:request', 'teacher:evaluation:view',
            # User permissions
            'user:view',
            # Dashboard
            'dashboard:view',
        ]
        
        teacher_count = 0
        for perm in teacher_perms:
            p = self.get_permission(perm)
            if p:
                teacher_group.permissions.add(p)
                teacher_count += 1
        self.stdout.write(f'✓ Teacher group: {teacher_count} permissions')
        
        # Student permissions
        student_perms = [
            'course:view',
            'assignment:view', 'assignment:submit',
            'grade:view',
            'schedule:view', 'schedule:attend',
            'student:view', 'student:attendance:view', 'student:progress:view',
            'student:documents:view', 'student:transcript:view',
            'parent:view',
            'fees:view', 'fees:pay',
            'dashboard:view',
        ]
        
        student_count = 0
        for perm in student_perms:
            p = self.get_permission(perm)
            if p:
                student_group.permissions.add(p)
                student_count += 1
        self.stdout.write(f'✓ Student group: {student_count} permissions')
        
        # Parent permissions
        parent_perms = [
            'course:view',
            'grade:view',
            'schedule:view',
            'student:view', 'student:attendance:view', 'student:progress:view',
            'student:behavior:view', 'student:transcript:view',
            'parent:view', 'parent:communicate', 'parent:meeting:schedule',
            'parent:progress:view', 'parent:fees:view', 'parent:fees:pay',
            'parent:attendance:view',
            'fees:view', 'fees:pay',
            'dashboard:view',
        ]
        
        parent_count = 0
        for perm in parent_perms:
            p = self.get_permission(perm)
            if p:
                parent_group.permissions.add(p)
                parent_count += 1
        self.stdout.write(f'✓ Parent group: {parent_count} permissions')
        
        # Staff permissions
        staff_perms = [
            'user:view', 'user:create', 'user:edit',
            'student:view', 'student:create', 'student:edit', 'student:enroll',
            'student:documents:view', 'student:documents:upload',
            'student:attendance:view', 'student:attendance:mark',
            'parent:view', 'parent:create', 'parent:edit', 'parent:communicate',
            'teacher:view', 'teacher:schedule:view',
            'staff:view', 'staff:schedule:view',
            'schedule:view', 'schedule:create', 'schedule:edit',
            'fees:view', 'fees:create', 'fees:edit', 'fees:report', 'fees:dues:track',
            'reports:view', 'reports:generate',
            'settings:view',
            'dashboard:view', 'dashboard:customize',
        ]
        
        staff_count = 0
        for perm in staff_perms:
            p = self.get_permission(perm)
            if p:
                staff_group.permissions.add(p)
                staff_count += 1
        self.stdout.write(f'✓ Staff group: {staff_count} permissions')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Groups and permissions setup completed!'))