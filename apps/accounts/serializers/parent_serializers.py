# apps/accounts/serializers/parent_serializers.py
from rest_framework import serializers
from apps.accounts.models import Parent, Student, User
from apps.accounts.serializers.student_serializers import StudentDetailSerializer, StudentListSerializer
from apps.applications.models import Application
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import timezone
import datetime
from apps.accounts.utils.student_utils import create_student




class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'first_name', 'last_name', 'phone']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class ParentProfileSerializer(serializers.ModelSerializer):
    """Detailed serializer for parent profile"""
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    children = serializers.SerializerMethodField()
    has_active_application = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()
    application_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Parent
        fields = [
            'user_id',
            'full_name',
            'email',
            'relationship',
            'occupation',
            'phone',
            'alternate_phone',
            'address',
            'children',
            'has_active_application',
            'application_status',
            'application_id',
        ]
    
    def get_children(self, obj):
        """Get children with simplified data for parents"""
        children = obj.children.all()
        return StudentListSerializer(children, many=True, context=self.context).data
    
    def get_has_active_application(self, obj):
        """Check if parent has an active application"""
        try:
            application = Application.objects.get(applicant=obj.user)
            return application.status not in ['completed', 'rejected']
        except Application.DoesNotExist:
            return False
    
    def get_application_status(self, obj):
        """Get current application status"""
        try:
            application = Application.objects.get(applicant=obj.user)
            return application.status
        except Application.DoesNotExist:
            return None
    
    def get_application_id(self, obj):
        """Get application ID if exists"""
        try:
            application = Application.objects.get(applicant=obj.user)
            return str(application.id)
        except Application.DoesNotExist:
            return None


class ParentListSerializer(serializers.ModelSerializer):
    """Serializer for listing parents (admin view)"""
    id = serializers.UUIDField(source='user.id', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    children_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = Parent
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'relationship',
            'children_count',
            'created_at',
        ]
    
    def get_children_count(self, obj):
        return obj.children.count()

class ParentChildSerializer(serializers.ModelSerializer):
    """Simplified serializer for parent viewing children"""
    id = serializers.UUIDField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    age = serializers.IntegerField(read_only=True)
    parent_name = serializers.SerializerMethodField()
    parent_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id',
            'student_id',
            'name',
            'email',
            'date_of_birth',
            'age',
            'gender',
            'enrollment_date',
            'status',
            'performance',
            'guardian_name',
            'guardian_phone',
            'guardian_email',
            'guardian_relationship',
            'phone',
            'address',
            'has_allergies',
            'allergy_details',
            'medical_conditions',
            'attendance_rate',
            'average_grade',
            'gpa',
            'parent_name',
            'parent_email',
        ]
    
    def get_parent_name(self, obj):
        """Get parent's full name"""
        if obj.parent:
            return obj.parent.user.get_full_name()
        return obj.guardian_name
    
    def get_parent_email(self, obj):
        """Get parent's email"""
        if obj.parent:
            return obj.parent.user.email
        return obj.guardian_email

class ParentUpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for parents to update their profile"""
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Parent
        fields = [
            'first_name',
            'last_name',
            'relationship',
            'occupation',
            'phone',
            'alternate_phone',
            'address',
        ]
    
    def update(self, instance, validated_data):
        # Update user fields
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            if 'first_name' in user_data:
                user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                user.last_name = user_data['last_name']
            user.save()
        
        # Update parent fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class ParentChildCreateSerializer(serializers.ModelSerializer):
    """Serializer for parents to add their own children (during registration)"""
    
    # Input fields (write-only)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True)
    gender = serializers.ChoiceField(choices=['male', 'female'], write_only=True)
    
    # Output fields (read-only)
    id = serializers.UUIDField(source='user.id', read_only=True)
    student_id = serializers.CharField(read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Student
        fields = [
            # Output fields (read-only)
            'id', 'student_id', 'full_name', 'email', 'status', 'created_at', 'updated_at',
            # Input fields (write-only)
            'first_name', 'last_name', 'date_of_birth', 'gender',
            # Common fields
            'has_allergies', 'allergy_details', 'medical_conditions',
            'phone', 'address', 'notes'
        ]
        read_only_fields = ['id', 'student_id', 'status', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Access request from context
        self.request = self.context.get('request')
    
    def get_parent(self):
        """Get the parent from the request"""
        if not self.request:
            raise serializers.ValidationError("Request context not found")
        parent = get_object_or_404(Parent, user=self.request.user)
        return parent
    
    def validate(self, attrs):
        """Validate that date_of_birth is appropriate"""
        if attrs.get('date_of_birth'):
            from datetime import date
            today = date.today()
            age = today.year - attrs['date_of_birth'].year - (
                (today.month, today.day) < (attrs['date_of_birth'].month, attrs['date_of_birth'].day)
            )
            if age < 2:
                raise serializers.ValidationError({"date_of_birth": "Student must be at least 2 years old"})
            if age > 18:
                raise serializers.ValidationError({"date_of_birth": "Student must be under 18 years old"})
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        # Get the parent
        parent = self.get_parent()
        
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        date_of_birth = validated_data.pop('date_of_birth')
        gender = validated_data.pop('gender')
        
        # Create student using utility
        student = create_student(
            first_name=first_name,
            last_name=last_name,
            email=None,  # Auto-generate
            password=None,  # Use default
            is_active=False,  # Inactive until approved
            parent=parent,
            status='pending',  # Pending approval
            date_of_birth=date_of_birth,
            gender=gender,
            **validated_data
        )
        
        return student


class ParentChildUpdateSerializer(serializers.ModelSerializer):
    """Serializer for parents to update their children (limited fields)"""
    class Meta:
        model = Student
        fields = [
            'guardian_name',
            'guardian_phone',
            'guardian_email',
            'guardian_relationship',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'phone',
            'address',
            'has_allergies',
            'allergy_details',
            'medical_conditions',
        ]