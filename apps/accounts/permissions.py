# apps/accounts/permissions.py
from rest_framework import permissions
from apps.accounts.models import Parent

class BasePermission(permissions.BasePermission):
    """Base permission class with helper methods"""
    
    def is_admin(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def is_teacher(self, request):
        return request.user.is_authenticated and request.user.role == 'teacher'
    
    def is_student(self, request):
        return request.user.is_authenticated and request.user.role == 'student'
    
    def is_parent(self, request):
        return request.user.is_authenticated and request.user.role == 'parent'
    
    def is_staff_member(self, request):
        return request.user.is_authenticated and request.user.role == 'staff'
    
    def is_owner_or_admin(self, request, obj):
        """Check if user is the owner of the object or an admin"""
        if not request.user.is_authenticated:
            return False
        if self.is_admin(request):
            return True
        
        # Check ownership for different object types
        if isinstance(obj, User):
            return obj.id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user.id == request.user.id
        return False

class IsAdmin(permissions.BasePermission):
    """Allows access only to admin users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsTeacher(permissions.BasePermission):
    """Allows access only to teachers"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


class IsParentOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow access to parents and admins.
    - Parents can only access their own data
    - Admins can access all data
    """
    
    def has_permission(self, request, view):
        # Allow if user is authenticated and is either parent or admin
        return (request.user and request.user.is_authenticated and 
                (request.user.role == 'parent' or request.user.role == 'admin'))
    
    def has_object_permission(self, request, view, obj):
        # For object-level permissions
        if request.user.role == 'admin':
            return True
        
        # Parents can only access their own children
        if request.user.role == 'parent':
            # Get the parent profile
            try:
                parent = Parent.objects.get(user=request.user)
                # Check if the student belongs to this parent
                return obj.parent_id == parent.id
            except Parent.DoesNotExist:
                return False
        
        return False

class IsStudent(permissions.BasePermission):
    """Allows access only to students"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'
    

class IsApplicant(permissions.BasePermission):
    """Allows access only to applicants"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'applicant'

class IsParent(permissions.BasePermission):
    """Allows access only to parents"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'parent'

class IsStaff(permissions.BasePermission):
    """Allows access only to staff members"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'staff'

class IsActive(permissions.BasePermission):
    """Allows access only to active users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active

class IsAdminOrTeacher(permissions.BasePermission):
    """Allows access to admin and teacher users"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher']

class IsAdminOrStaff(permissions.BasePermission):
    """Allows access to admin and staff users"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class IsTeacherOrStudent(permissions.BasePermission):
    """Allows access to teacher and student users"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['teacher', 'student']

# User Management Permissions
class CanManageUsers(BasePermission):
    """Permission to manage users (create, edit, delete)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage all users, staff can manage non-admin users
        if self.is_admin(request):
            return True
        if self.is_staff_member(request):
            return obj.role != 'admin'
        return False

class CanViewUsers(BasePermission):
    """Permission to view users"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']

class CanActivateUsers(permissions.BasePermission):
    """Permission to activate/deactivate users"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

# Teacher Management Permissions
class CanViewTeachers(permissions.BasePermission):
    """Permission to view teachers"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff', 'student', 'parent']

class CanManageTeachers(permissions.BasePermission):
    """Permission to manage teachers (create, edit, delete)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'

class CanViewTeacherPerformance(BasePermission):
    """Permission to view teacher performance"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_staff_member(request):
            return True
        # Teachers can view their own performance
        if self.is_teacher(request) and hasattr(obj, 'user'):
            return obj.user.id == request.user.id
        return False

# Student Management Permissions
class CanViewStudents(BasePermission):
    """Permission to view students"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_teacher(request) or self.is_staff_member(request):
            return True
        # Parents can view their own children
        if self.is_parent(request) and hasattr(obj, 'user'):
            return obj in request.user.parent_profile.children.all()
        # Students can view themselves
        if self.is_student(request) and hasattr(obj, 'user'):
            return obj.user.id == request.user.id
        return False

class CanManageStudents(permissions.BasePermission):
    """Permission to manage students (create, edit, delete, enroll)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff', 'parent']
    
class CanManageStudentDocuments(permissions.BasePermission):
    """Permission to manage students documents"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class CanMarkAttendance(permissions.BasePermission):
    """Permission to mark attendance"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']

class CanViewAttendance(BasePermission):
    """Permission to view attendance"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True  # All authenticated users can view attendance
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_teacher(request) or self.is_staff_member(request):
            return True
        if self.is_student(request) and hasattr(obj, 'student'):
            return obj.student.user.id == request.user.id
        if self.is_parent(request) and hasattr(obj, 'student'):
            return obj.student in request.user.parent_profile.children.all()
        return False

class CanViewStudentProgress(BasePermission):
    """Permission to view student progress"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_teacher(request) or self.is_staff_member(request):
            return True
        if self.is_student(request) and hasattr(obj, 'user'):
            return obj.user.id == request.user.id
        if self.is_parent(request) and hasattr(obj, 'user'):
            return obj in request.user.parent_profile.children.all()
        return False

class CanEnrollStudents(BasePermission):
    """Permission to view students"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']
   

# Parent Management Permissions
class CanViewParents(permissions.BasePermission):
    """Permission to view parents"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']

class CanManageParents(permissions.BasePermission):
    """Permission to manage parents (create, edit, delete)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class CanCommunicateWithParents(permissions.BasePermission):
    """Permission to communicate with parents"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'teacher', 'staff']

# couse management permissions

class CanManageCourses(permissions.BasePermission):
    """Permission to manage courses"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff', 'teacher']
    
class CanViewCourses(permissions.BasePermission):
    """Permission to view staff"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

# Staff Management Permissions
class CanViewStaff(permissions.BasePermission):
    """Permission to view staff"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class CanManageStaff(permissions.BasePermission):
    """Permission to manage staff (create, edit, delete)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'

# Report Permissions
class CanViewReports(permissions.BasePermission):
    """Permission to view reports"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class CanGenerateReports(permissions.BasePermission):
    """Permission to generate reports"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

# Settings Permissions
class CanViewSettings(permissions.BasePermission):
    """Permission to view settings"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

class CanEditSettings(permissions.BasePermission):
    """Permission to edit settings"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'

# Dashboard Permissions
class CanViewDashboard(permissions.BasePermission):
    """Permission to view dashboard"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated

class CanCustomizeDashboard(permissions.BasePermission):
    """Permission to customize dashboard"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'staff']

# Object Ownership Permissions
class IsOwnerOrAdmin(BasePermission):
    """Allows access only to object owners or admins"""
    
    def has_object_permission(self, request, view, obj):
        return self.is_owner_or_admin(request, obj)

class IsOwnerOrTeacherOrAdmin(BasePermission):
    """Allows access to owners, teachers, and admins"""
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_teacher(request):
            return True
        return self.is_owner_or_admin(request, obj)

class IsOwnerOrParentOrTeacherOrAdmin(BasePermission):
    """Allows access to owners, parents of the student, teachers, and admins"""
    
    def has_object_permission(self, request, view, obj):
        if self.is_admin(request) or self.is_teacher(request):
            return True
        if self.is_owner_or_admin(request, obj):
            return True
        # Check if user is parent of the student
        if self.is_parent(request) and hasattr(obj, 'student'):
            return obj.student in request.user.parent_profile.children.all()
        return False

# Role-based viewset permissions
class RolePermissions(permissions.BasePermission):
    """
    Generic permission class that maps viewset actions to required roles
    """
    
    def __init__(self, action_roles=None):
        self.action_roles = action_roles or {
            'list': ['admin', 'teacher', 'staff'],
            'create': ['admin', 'staff'],
            'retrieve': ['admin', 'teacher', 'staff', 'student', 'parent'],
            'update': ['admin', 'staff'],
            'partial_update': ['admin', 'staff'],
            'destroy': ['admin'],
        }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if view.action in self.action_roles:
            return request.user.role in self.action_roles[view.action]
        
        return False