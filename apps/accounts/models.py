# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel
import uuid
from django.contrib.auth.models import Permission

class User(AbstractUser):
    """Custom user model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False) 
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
        ('applicant', 'Applicant'),
    ])
    is_active = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email', 'role']),
        ]
        permissions = [
            # Course permissions
            ("course:view", "Can view courses"),
            ("course:create", "Can create courses"),
            ("course:edit", "Can edit courses"),
            ("course:delete", "Can delete courses"),
            ("course:enroll", "Can enroll in courses"),
            ("course:manage", "Can manage courses"),
            
            # Assignment permissions
            ("assignment:view", "Can view assignments"),
            ("assignment:create", "Can create assignments"),
            ("assignment:edit", "Can edit assignments"),
            ("assignment:delete", "Can delete assignments"),
            ("assignment:submit", "Can submit assignments"),
            ("assignment:grade", "Can grade assignments"),
            
            # Grade permissions
            ("grade:view", "Can view grades"),
            ("grade:edit", "Can edit grades"),
            ("grade:manage", "Can manage grades"),
            
            # Schedule permissions
            ("schedule:view", "Can view schedule"),
            ("schedule:create", "Can create schedule"),
            ("schedule:edit", "Can edit schedule"),
            ("schedule:delete", "Can delete schedule"),
            ("schedule:manage", "Can manage schedule"),
            ("schedule:book", "Can book appointments"),
            ("schedule:attend", "Can mark attendance"),
            
            # Fees/Finance permissions
            ("fees:view", "Can view fees"),
            ("fees:create", "Can create fees"),
            ("fees:edit", "Can edit fees"),
            ("fees:delete", "Can delete fees"),
            ("fees:manage", "Can manage fees"),
            ("fees:pay", "Can pay fees"),
            ("fees:refund", "Can refund fees"),
            ("fees:report", "Can generate fee reports"),
            ("fees:structure:view", "Can view fee structure"),
            ("fees:structure:edit", "Can edit fee structure"),
            ("fees:discount:apply", "Can apply discounts"),
            ("fees:dues:track", "Can track dues"),
            
            # Staff management permissions
            ("staff:view", "Can view staff"),
            ("staff:create", "Can create staff"),
            ("staff:edit", "Can edit staff"),
            ("staff:delete", "Can delete staff"),
            ("staff:manage", "Can manage staff"),
            ("staff:schedule:view", "Can view staff schedule"),
            ("staff:schedule:edit", "Can edit staff schedule"),
            ("staff:performance:view", "Can view staff performance"),
            ("staff:performance:edit", "Can edit staff performance"),
            ("staff:leave:view", "Can view staff leave"),
            ("staff:leave:approve", "Can approve staff leave"),
            ("staff:leave:request", "Can request leave"),
            ("staff:documents:view", "Can view staff documents"),
            ("staff:documents:upload", "Can upload staff documents"),
            
            # Parent management permissions
            ("parent:view", "Can view parents"),
            ("parent:create", "Can create parents"),
            ("parent:edit", "Can edit parents"),
            ("parent:delete", "Can delete parents"),
            ("parent:manage", "Can manage parents"),
            ("parent:communicate", "Can communicate with parents"),
            ("parent:meeting:schedule", "Can schedule parent meetings"),
            ("parent:progress:view", "Can view parent progress reports"),
            ("parent:fees:view", "Can view parent fees"),
            ("parent:fees:pay", "Can pay parent fees"),
            ("parent:attendance:view", "Can view parent attendance"),

            # application management permissions
            # 'application:view', 'application:create', 'application:edit', 'application:submit',
            ("application:view", "Can view application"),
            ("application:edit", "Can edit application"),
            ("application:create", "Can create application"),
            ("application:submit", "Can submit application"),
            ("application:approve", "Can approve application"),
            
            # Student management permissions
            ("student:view", "Can view students"),
            ("student:create", "Can create students"),
            ("student:edit", "Can edit students"),
            ("student:delete", "Can delete students"),
            ("student:manage", "Can manage students"),
            ("student:enroll", "Can enroll students"),
            ("student:withdraw", "Can withdraw students"),
            ("student:attendance:view", "Can view student attendance"),
            ("student:attendance:mark", "Can mark student attendance"),
            ("student:progress:view", "Can view student progress"),
            ("student:progress:edit", "Can edit student progress"),
            ("student:behavior:view", "Can view student behavior"),
            ("student:behavior:report", "Can report student behavior"),
            ("student:documents:view", "Can view student documents"),
            ("student:documents:upload", "Can upload student documents"),
            ("student:transcript:view", "Can view student transcript"),
            ("student:transcript:generate", "Can generate student transcript"),
            
            # Teacher management permissions
            ("teacher:view", "Can view teachers"),
            ("teacher:create", "Can create teachers"),
            ("teacher:edit", "Can edit teachers"),
            ("teacher:delete", "Can delete teachers"),
            ("teacher:manage", "Can manage teachers"),
            ("teacher:schedule:view", "Can view teacher schedule"),
            ("teacher:schedule:edit", "Can edit teacher schedule"),
            ("teacher:performance:view", "Can view teacher performance"),
            ("teacher:performance:edit", "Can edit teacher performance"),
            ("teacher:leave:view", "Can view teacher leave"),
            ("teacher:leave:approve", "Can approve teacher leave"),
            ("teacher:leave:request", "Can request leave"),
            ("teacher:courses:assign", "Can assign courses to teachers"),
            ("teacher:evaluation:view", "Can view teacher evaluations"),
            ("teacher:evaluation:submit", "Can submit teacher evaluations"),
            
            # User permissions
            ("user:view", "Can view users"),
            ("user:create", "Can create users"),
            ("user:edit", "Can edit users"),
            ("user:delete", "Can delete users"),
            ("user:manage", "Can manage users"),
            
            # System permissions
            ("settings:view", "Can view settings"),
            ("settings:edit", "Can edit settings"),
            ("reports:view", "Can view reports"),
            ("reports:generate", "Can generate reports"),
            ("dashboard:view", "Can view dashboard"),
            ("dashboard:customize", "Can customize dashboard"),
        ]

    def __str__(self):
        return f"{self.email} - {self.role}"
    
    def save(self, *args, **kwargs):
        # Auto-create username from email if not provided
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    def get_permissions_list(self):
        """Get all permissions for this user from groups"""
        if not self.is_authenticated:
            return []
        
        perms = set()
        for group in self.groups.all():
            for perm in group.permissions.all():
                # Extract just the codename (remove app prefix)
                codename = perm.codename
                perms.add(codename)
        
        if self.role == 'admin':
            all_perms = Permission.objects.values_list('codename', flat=True)
            perms.update(all_perms)
        
        return list(perms)

class GradeLevel(models.Model):
    """Represents a grade level (Grade 2 through 10) - for Islamic school ages 7-15"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)  # e.g., "Grade 2", "Grade 3"
    level_number = models.IntegerField(unique=True)  # 2, 3, 4, ... 10
    display_name = models.CharField(max_length=100, blank=True)  # e.g., "Grade 2 (Ages 7-8)"
    min_age = models.IntegerField(default=7)
    max_age = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # For custom ordering
    
    class Meta:
        db_table = 'grade_levels'
        ordering = ['level_number']
    
    def save(self, *args, **kwargs):
        if not self.display_name:
            age_range = f"Ages {self.min_age}-{self.max_age}"
            self.display_name = f"{self.name} ({age_range})"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.display_name

class Student(models.Model):
    """Student profile - enhanced to match frontend needs"""

    STUDENT_DEFAULT_PASSWORD = "Student@miia100."
    
    # Performance levels matching frontend
    PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('needs-improvement', 'Needs Improvement'),
        ('at-risk', 'At Risk'),
    ]
    
    # Keep existing fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    enrollment_date = models.DateField(null=True, blank=True)
    
    # Enhanced fields
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
    ], blank=True)

    parent = models.ForeignKey(
        'Parent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    

    
    
    # Grade level (new)
    # current_grade = models.ForeignKey(
    #     GradeLevel, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True,
    #     related_name='students'
    # )
    
    # Performance tracking
    performance = models.CharField(
        max_length=20, 
        choices=PERFORMANCE_CHOICES, 
        default='average'
    )
    
    # Academic info
    department = models.CharField(max_length=100, blank=True)  # e.g., "Elementary", "Middle School"
    
    # Guardian/Parent info - enhance existing guardian fields
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)  # mother, father, guardian
    
    # Emergency contact (separate from guardian)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Contact info
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)  # student's own phone if applicable
    
    # Advisor (teacher)
    advisor = models.ForeignKey(
        'Teacher', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='advisees'
    )
    
    # Status (enhance existing)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Enrollment'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Academic dates
    graduation_date = models.DateField(null=True, blank=True)
    
    # Medical info
    has_allergies = models.BooleanField(default=False)
    allergy_details = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # Tracking
    last_active = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['status']),
            # models.Index(fields=['current_grade']),
            models.Index(fields=['performance']),
        ]
        permissions = [
            ("can_view_student_progress", "Can view student progress"),
            ("can_edit_student_progress", "Can edit student progress"),
            ("can_mark_attendance", "Can mark attendance"),
            ("can_view_attendance", "Can view attendance"),
            ("can_report_behavior", "Can report behavior"),
            ("can_view_behavior", "Can view behavior"),
            ("can_manage_student_documents", "Can manage student documents"),
            ("can_view_student_documents", "Can view student documents"),
            ("can_enroll_students", "Can enroll students"),
            ("can_withdraw_students", "Can withdraw students"),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"
    
    @property
    def name(self):
        """Match frontend's name field"""
        return self.user.get_full_name()
    
    @property
    def email(self):
        """Match frontend's email field"""
        return self.user.email
    
    @property
    def avatar(self):
        """Match frontend's avatar field"""
        return self.user.profile_picture.url if self.user.profile_picture else None
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def enrolled_courses_count(self):
        """Count of currently enrolled courses"""
        # This will be implemented when academics app is created
        return 0
    
    @property
    def attendance_rate(self):
        """Placeholder - will be implemented with attendance app"""
        return 0
    
    @property
    def average_grade(self):
        """Placeholder - will be implemented with grades app"""
        return 0
    
    @property
    def gpa(self):
        """Placeholder - will be implemented with grades app"""
        return 0.0
    
    @property
    def parent_name(self):
        """Get parent's full name"""
        if self.parent:
            return self.parent.user.get_full_name()
        return self.guardian_name
    
    @property
    def parent_email(self):
        """Get parent's email"""
        if self.parent:
            return self.parent.user.email
        return self.guardian_email
    
    @property
    def parent_phone(self):
        """Get parent's phone"""
        if self.parent:
            return self.parent.phone
        return self.guardian_phone


class StudentDocument(models.Model):
    """Documents uploaded for students (birth certificate, health records, etc.)"""
    DOCUMENT_TYPES = [
        ('birth_certificate', 'Birth Certificate'),
        ('health_record', 'Health Record'),
        ('previous_school', 'Previous School Records'),
        ('identification', 'Identification'),
        ('medical', 'Medical Information'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='student_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'student_documents'
        ordering = ['-uploaded_at']


class StudentNote(models.Model):
    """Internal notes about students (for teachers/advisors)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_private = models.BooleanField(default=True)  # Private notes only visible to staff
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_notes'
        ordering = ['-created_at']


class Teacher(models.Model):
    """Teacher profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    qualification = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    joining_date = models.DateField()
    
    class Meta:
        db_table = 'teachers'
        permissions = [
            ("can_view_teacher_performance", "Can view teacher performance"),
            ("can_edit_teacher_performance", "Can edit teacher performance"),
            ("can_manage_teacher_schedule", "Can manage teacher schedule"),
            ("can_approve_teacher_leave", "Can approve teacher leave"),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"


class Parent(models.Model):
    """Parent profile - updated to work with enhanced Student"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='parent_profile')
    occupation = models.CharField(max_length=255, blank=True)
    relationship = models.CharField(max_length=50)  # mother, father, guardian
    # children = models.ManyToManyField(Student, related_name='parents', blank=True)
    
    # Additional parent info
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    class Meta:
        db_table = 'parents'
        permissions = [
            ("can_view_parent_details", "Can view parent details"),
            ("can_edit_parent_details", "Can edit parent details"),
            ("can_communicate_with_parents", "Can communicate with parents"),
            ("can_schedule_parent_meetings", "Can schedule parent meetings"),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.relationship}"
    
    @property
    def name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email

class Staff(models.Model):
    """Staff profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='staff_profile')
    staff_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    joining_date = models.DateField()
    
    class Meta:
        db_table = 'staff'
        permissions = [
            ("can_view_staff_performance", "Can view staff performance"),
            ("can_edit_staff_performance", "Can edit staff performance"),
            ("can_manage_staff_schedule", "Can manage staff schedule"),
            ("can_approve_staff_leave", "Can approve staff leave"),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.staff_id}"