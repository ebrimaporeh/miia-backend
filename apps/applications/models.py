# apps/applications/models.py
from django.db import models
from apps.core.models import TimeStampedModel
import uuid

class Application(TimeStampedModel):
    """Tracks the student registration application process"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft - Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted - Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed - Student Enrolled'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Legal Guardian'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The applicant (user with role='applicant')
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    # Link to existing Parent record (created after approval)
    parent = models.ForeignKey(
        'accounts.Parent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    
    # Terms
    # terms_accepted = models.BooleanField(default=False)
    # privacy_accepted = models.BooleanField(default=False)
    
    # Tracking
    current_step = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Admin review
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"Application {self.id} - {self.applicant.email} - {self.status}"
    
    @property
    def has_parent_info(self):
        """Check if parent info has been filled"""
        return hasattr(self, 'applicant_parent')
    
    @property
    def children_count(self):
        """Count of children in this application"""
        return self.applicant_children.count()
    
    @property
    def is_complete(self):
        """Check if application is ready for submission"""
        return (
            self.has_parent_info and 
            self.children_count > 0 and 
            self.terms_accepted and 
            self.privacy_accepted
        )


class ApplicantParent(models.Model):
    """Temporary parent/guardian information for an application"""
    
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Legal Guardian'),
    ]
    
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='applicant_parent'
    )
    
    # Parent/Guardian Information
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    occupation = models.CharField(max_length=255, blank=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applicant_parents'
        verbose_name = 'Applicant Parent'
        verbose_name_plural = 'Applicant Parents'
    
    def __str__(self):
        return f"Parent for {self.application.applicant.email}: {self.full_name}"
    
    @property
    def first_name(self):
        return self.full_name.split()[0] if self.full_name else ''
    
    @property
    def last_name(self):
        parts = self.full_name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''


class ApplicantChild(models.Model):
    """Temporary child information for an application"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='applicant_children'
    )
    
    # Child Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Optional fields
    nationality = models.CharField(max_length=100, blank=True)
    
    # Medical Information
    has_allergies = models.BooleanField(default=False)
    allergy_details = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # Contact Information (if different from parent)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Additional Notes
    notes = models.TextField(blank=True)
    
    # Order for display
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applicant_children'
        ordering = ['order', 'created_at']
        verbose_name = 'Applicant Child'
        verbose_name_plural = 'Applicant Children'
    
    def __str__(self):
        return f"Child for {self.application.applicant.email}: {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None