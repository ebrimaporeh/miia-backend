from django.db import models
import uuid

class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class BasePersonModel(TimeStampedModel):
    """Abstract base for person-related models"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('M', 'Male'), ('F', 'Female')],
        blank=True
    )
    
    class Meta:
        abstract = True
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"