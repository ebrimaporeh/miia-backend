# apps/academics/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import Teacher, Student, GradeLevel
import uuid


class AcademicYear(models.Model):
    """Academic year (e.g., 2024-2025)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)  # "2024-2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name


class Term(models.Model):
    """Academic term (e.g., Term 1, Term 2)"""
    TERM_TYPES = [
        ('term1', 'Term 1'),
        ('term2', 'Term 2'),
        ('term3', 'Term 3'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=50)
    term_type = models.CharField(max_length=20, choices=TERM_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'terms'
        ordering = ['start_date']
        unique_together = ['academic_year', 'term_type']
    
    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"


class Subject(models.Model):
    """Subject that can be taught - includes both Islamic and conventional"""
    CATEGORY_CHOICES = [
        # Islamic Studies
        ('quran', 'Quran'),
        ('tajweed', 'Tajweed'),
        ('tahfiz', 'Tahfiz (Memorization)'),
        ('arabic', 'Arabic Language'),
        ('islamic_history', 'Islamic History'),
        ('aqeedah', 'Aqeedah'),
        ('fiqh', 'Fiqh'),
        ('seerah', 'Seerah'),
        ('adab', 'Adab (Islamic Ethics)'),
        
        # Conventional Subjects
        ('mathematics', 'Mathematics'),
        ('english', 'English Language'),
        ('science', 'Science'),
        ('social_studies', 'Social Studies'),
        ('malay', 'Malay Language'),
        ('physical_education', 'Physical Education'),
        ('arts', 'Arts'),
        ('ict', 'Information Technology'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # For Islamic subjects
    is_islamic = models.BooleanField(default=False)
    requires_memorization = models.BooleanField(default=False)  # For Quran/Tahfiz
    
    class Meta:
        db_table = 'subjects'
        ordering = ['name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_islamic']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    """Course/Class - matches frontend Course interface"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
        ('draft', 'Draft'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core fields
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    
    # Relationships
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.PROTECT, 
        related_name='courses'
    )
    instructor = models.ForeignKey(
        Teacher, 
        on_delete=models.PROTECT, 
        related_name='courses_taught'
    )
    grade_level = models.ForeignKey(
        GradeLevel, 
        on_delete=models.PROTECT, 
        related_name='courses'
    )
    
    # Academic Info
    credits = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    # Schedule
    schedule = models.CharField(max_length=255, blank=True)  # e.g., "Mon/Wed 9:00-10:30"
    duration = models.CharField(max_length=50, blank=True)  # e.g., "16 weeks"
    room = models.CharField(max_length=50, blank=True)
    
    # Capacity
    max_students = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    current_students = models.IntegerField(default=0)
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Course materials (JSON fields for flexibility)
    prerequisites = models.JSONField(default=list, blank=True)
    objectives = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # UI
    color = models.CharField(max_length=20, blank=True)  # For frontend display
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['subject']),
            models.Index(fields=['instructor']),
        ]
        ordering = ['title']
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    @property
    def instructor_name(self):
        """Get instructor full name"""
        return self.instructor.user.get_full_name() if self.instructor else ""
    
    @property
    def students_count(self):
        """Current number of enrolled students"""
        return self.current_students
    
    @property
    def assignments_due(self):
        """Count of assignments due soon"""
        # Will be implemented with assignments app
        return 0


class CourseMaterial(models.Model):
    """Course materials - matches frontend CourseMaterial interface"""
    TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('ppt', 'Presentation'),
        ('video', 'Video'),
        ('link', 'Link'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='course_materials/%Y/%m/', null=True, blank=True)
    url = models.URLField(blank=True)
    size = models.CharField(max_length=20, blank=True)  # e.g., "2.4 MB"
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'course_materials'
        ordering = ['-uploaded_at']


class CourseAnnouncement(models.Model):
    """Course announcements - matches frontend CourseAnnouncement interface"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    attachments = models.JSONField(default=list, blank=True)  # List of attachment URLs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_announcements'
        ordering = ['-created_at']


class Enrollment(models.Model):
    """Course enrollment - matches frontend CourseEnrollment interface"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('pending', 'Pending'),
        ('waitlisted', 'Waitlisted'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    
    # Progress tracking
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Grade info (will be populated by grading system)
    final_grade = models.CharField(max_length=5, blank=True)  # e.g., "A", "B+"
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course']  # Prevent duplicate enrollments
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code}"
    
    @property
    def student_name(self):
        return self.student.name
    
    @property
    def course_code(self):
        return self.course.code
    
    @property
    def course_title(self):
        return self.course.title