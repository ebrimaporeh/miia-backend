# apps/applications/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.applications.models import Application
from apps.accounts.models import Parent, Student
from apps.accounts.serializers.student_serializers import StudentDetailSerializer
from apps.accounts.serializers.parent_serializers import ParentProfileSerializer

User = get_user_model()

class ApplicationSerializer(serializers.ModelSerializer):
    """Main serializer for Application"""
    parent_detail = ParentProfileSerializer(source='parent', read_only=True)
    children_detail = StudentDetailSerializer(source='children', many=True, read_only=True)
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'status', 'current_step', 
            'applicant', 'applicant_name', 'applicant_email',
            'parent', 'parent_detail', 
            'children', 'children_detail',
            'terms_accepted', 'privacy_accepted',
            'created_at', 'updated_at', 'submitted_at',
            'reviewed_by', 'reviewed_at', 'review_notes', 'rejection_reason'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'submitted_at']
    
    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.email

class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    parent_name = serializers.CharField(source='parent.user.get_full_name', read_only=True)
    children_names = serializers.SerializerMethodField()
    children_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'applicant_name', 'applicant_email', 
            'parent_name', 'children_names', 'children_count',
            'status', 'current_step', 'created_at', 'submitted_at'
        ]
    
    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.email
    
    def get_children_names(self, obj):
        return [child.user.get_full_name() for child in obj.children.all()]

class CreateApplicationSerializer(serializers.Serializer):
    """Serializer for creating application (Step 1 - Account Creation)"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        return attrs
    
    def create(self, validated_data):
        # Extract user data
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone = validated_data.pop('phone', '')
        
        # Create username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create the parent user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='parent',
            phone=phone,
            is_active=True
        )
        
        # Create the application
        application = Application.objects.create(
            applicant=user,
            status='in_progress',
            current_step=1
        )
        
        return application

class UpdateApplicationSerializer(serializers.ModelSerializer):
    """Serializer for updating application (Steps 2-5)"""
    children = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        many=True,
        required=False
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(),
        required=False
    )
    
    class Meta:
        model = Application
        fields = [
            'current_step', 'parent', 'children',
            'terms_accepted', 'privacy_accepted'
        ]

class SubmitApplicationSerializer(serializers.Serializer):
    """Serializer for final submission"""
    
    def validate(self, attrs):
        instance = self.instance
        
        # Validate that parent is linked
        if not instance.parent:
            raise serializers.ValidationError({"parent": "Parent information is required before submission."})
        
        # Validate that at least one child is linked
        if not instance.children.exists():
            raise serializers.ValidationError({"children": "At least one child is required before submission."})
        
        if not instance.terms_accepted:
            raise serializers.ValidationError({"terms_accepted": "You must accept the terms and conditions."})
        
        if not instance.privacy_accepted:
            raise serializers.ValidationError({"privacy_accepted": "You must accept the privacy policy."})
        
        return attrs
    
    def update(self, instance, validated_data):
        instance.status = 'submitted'
        instance.current_step = 6
        from django.utils import timezone
        instance.submitted_at = timezone.now()
        instance.save()
        return instance

class ReviewApplicationSerializer(serializers.Serializer):
    """Serializer for admin review"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    review_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        action = validated_data.get('action')
        review_notes = validated_data.get('review_notes', '')
        
        from django.utils import timezone
        
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        instance.review_notes = review_notes
        
        if action == 'approve':
            instance.status = 'approved'
            # Activate the parent and all children
            if instance.parent:
                instance.parent.user.is_active = True
                instance.parent.user.save()
            
            for child in instance.children.all():
                child.status = 'active'
                child.save()
        else:
            instance.status = 'rejected'
            instance.rejection_reason = validated_data.get('rejection_reason', '')
        
        instance.save()
        return instance