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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The parent/guardian creating this application
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
    
    # Link to existing Student records (multiple children)
    children = models.ManyToManyField(
        'accounts.Student',
        blank=True,
        related_name='applications'
    )
    
    # Terms
    terms_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)
    
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
    def children_count(self):
        return self.children.count()