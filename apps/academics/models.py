# apps/academics/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
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
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other academic years to not current
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


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
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other terms in same academic year to not current
            Term.objects.filter(academic_year=self.academic_year, is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


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
            models.Index(fields=['academic_year', 'term']),
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
    def available_seats(self):
        """Number of available seats"""
        return self.max_students - self.current_students
    
    @property
    def is_full(self):
        """Check if course is full"""
        return self.current_students >= self.max_students


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
    file = models.FileField(
        upload_to='course_materials/%Y/%m/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'zip'])]
    )
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


# ========== ASSESSMENT MODELS ==========

class Assessment(models.Model):
    """Base assessment model - quizzes, exams, assignments"""
    
    TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('participation', 'Participation'),
        ('homework', 'Homework'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('grading', 'Grading'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Relationships
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_assessments')
    
    # Grading
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage weight towards final grade")
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    
    # Duration (for timed assessments)
    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    
    # Settings
    attempts_allowed = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    allow_late_submission = models.BooleanField(default=False)
    late_submission_days = models.IntegerField(default=0)
    late_penalty_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Grading settings
    auto_grade = models.BooleanField(default=False, help_text="Whether assessment can be auto-graded")
    rubric_id = models.UUIDField(null=True, blank=True, help_text="Reference to rubric if used")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    
    # Visibility
    show_answers_after_due = models.BooleanField(default=False)
    show_scores_immediately = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments'
        indexes = [
            models.Index(fields=['course', 'type']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['course', 'due_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def is_timed(self):
        return self.time_limit_minutes is not None
    
    @property
    def is_open(self):
        from django.utils import timezone
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return self.status in ['published', 'active']


class Question(models.Model):
    """Questions for assessments (quizzes/exams)"""
    
    TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('matching', 'Matching'),
        ('fill_blank', 'Fill in the Blank'),
        ('file_upload', 'File Upload'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    
    # Question content
    text = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Points
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    
    # For multiple choice and matching
    options = models.JSONField(default=list, blank=True, help_text="List of options for multiple choice")
    correct_answer = models.JSONField(default=list, blank=True, help_text="Correct answer(s)")
    
    # For essay and short answer
    sample_answer = models.TextField(blank=True, help_text="Sample answer for grading reference")
    max_words = models.IntegerField(null=True, blank=True)
    
    # For file upload
    allowed_file_types = models.JSONField(default=list, blank=True, help_text="List of allowed file extensions")
    
    # Metadata
    explanation = models.TextField(blank=True, help_text="Explanation for correct answer")
    hint = models.TextField(blank=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'questions'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['assessment', 'type']),
        ]
    
    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"


class Submission(models.Model):
    """Student submission for an assessment"""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('late', 'Late'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    
    # Submission data
    answers_data = models.JSONField(default=dict, help_text="Structured answers for each question")
    attachments = models.JSONField(default=list, blank=True, help_text="Uploaded files")
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    # Attempt tracking
    attempt_number = models.IntegerField(default=1)
    
    # Grading
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # For auto-grading
    auto_grade_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'submissions'
        unique_together = ['assessment', 'student', 'attempt_number']
        indexes = [
            models.Index(fields=['assessment', 'student']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.assessment.title}"
    
    @property
    def is_late(self):
        from django.utils import timezone
        if self.assessment.due_date and self.submitted_at:
            return self.submitted_at > self.assessment.due_date
        return False


class Answer(models.Model):
    """Individual answer for a question in a submission"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answer_items') 
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    
    # Answer content
    answer_text = models.TextField(blank=True)
    answer_choice = models.JSONField(default=list, blank=True)
    file_attachments = models.JSONField(default=list, blank=True)
    
    # Grading
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    
    # For essay grading
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'answers'
        unique_together = ['submission', 'question']
    
    def __str__(self):
        return f"{self.submission.id} - {self.question.id}"


class Grade(models.Model):
    """Overall grade for a student in a course"""
    
    GRADE_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D', 'D'), ('F', 'F'),
        ('I', 'Incomplete'), ('W', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    
    # Grade components
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    letter_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    gpa_points = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Breakdown by assessment type
    quiz_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    exam_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assignment_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    project_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    participation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Additional info
    comments = models.TextField(blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'grades'
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'letter_grade']),
            models.Index(fields=['course', 'letter_grade']),
        ]
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code}: {self.letter_grade}"
    
    def calculate_letter_grade(self):
        """Convert percentage to letter grade"""
        percentage = float(self.total_score) if self.total_score else 0
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'


class Attendance(models.Model):
    """Student attendance tracking"""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('holiday', 'Holiday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Tracking
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendances'
        unique_together = ['student', 'course', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['course', 'date']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} - {self.date}: {self.status}"


class GradeScale(models.Model):
    """Grade scale configuration for the institution"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=2)
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    gpa_points = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'grade_scales'
        ordering = ['-min_percentage']
        unique_together = ['name', 'grade']
    
    def __str__(self):
        return f"{self.grade}: {self.min_percentage}% - {self.max_percentage}%"