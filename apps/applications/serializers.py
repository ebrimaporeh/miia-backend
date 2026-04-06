# apps/applications/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.applications.models import Application, ApplicantParent, ApplicantChild
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils import timezone
from .tasks import create_parent_and_students_from_application_task, send_application_rejected_email_task
from django.utils import timezone
from django.db import transaction

User = get_user_model()


class ApplicantParentSerializer(serializers.ModelSerializer):
    """Serializer for applicant parent/guardian information"""
    
    class Meta:
        model = ApplicantParent
        fields = [
            'full_name', 'email', 'phone', 'alternate_phone',
            'address', 'occupation', 'relationship',
            'first_name', 'last_name'
        ]


class ApplicantChildSerializer(serializers.ModelSerializer):
    """Serializer for applicant child information"""
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ApplicantChild
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'nationality',
            'has_allergies', 'allergy_details', 'medical_conditions',
            'phone', 'address', 'notes', 'order'
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for application with parent and children data"""
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    parent = ApplicantParentSerializer(source='applicant_parent', read_only=True)
    children = ApplicantChildSerializer(source='applicant_children', many=True, read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'status', 'current_step', 'applicant', 'applicant_email', 'applicant_name',
            'parent', 'children', 'children_count', 'is_complete',
            'terms_accepted', 'privacy_accepted',
            'created_at', 'updated_at', 'submitted_at',
            'reviewed_by', 'reviewed_at', 'review_notes', 'rejection_reason'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'submitted_at']


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    parent_name = serializers.CharField(source='applicant_parent.full_name', read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'applicant_name', 'applicant_email', 'parent_name',
            'children_count', 'status', 'current_step', 'created_at', 'submitted_at'
        ]


class ApplicationParentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating parent information (Step 1)"""
    
    class Meta:
        model = ApplicantParent
        fields = [
            'full_name', 'email', 'phone', 'alternate_phone',
            'address', 'occupation', 'relationship'
        ]


class ApplicationChildCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a child (Step 2)"""
    
    class Meta:
        model = ApplicantChild
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'nationality',
            'has_allergies', 'allergy_details', 'medical_conditions',
            'phone', 'address', 'notes'
        ]


class ApplicationChildUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a child"""
    
    class Meta:
        model = ApplicantChild
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'nationality',
            'has_allergies', 'allergy_details', 'medical_conditions',
            'phone', 'address', 'notes', 'order'
        ]


class ApplicationSubmitSerializer(serializers.Serializer):
    """Serializer for final submission (Step 3)"""
    
    def validate(self, attrs):
        instance = self.instance
        
        if not instance.has_parent_info:
            raise serializers.ValidationError({"parent": "Parent/guardian information is required."})
        
        if instance.children_count == 0:
            raise serializers.ValidationError({"children": "At least one child is required."})
        
        # if not instance.terms_accepted:
        #     raise serializers.ValidationError({"terms_accepted": "You must accept the terms and conditions."})
        
        # if not instance.privacy_accepted:
        #     raise serializers.ValidationError({"privacy_accepted": "You must accept the privacy policy."})
        
        return attrs
    
    def update(self, instance, validated_data):
        instance.status = 'submitted'
        instance.current_step = 3
        instance.submitted_at = timezone.now()
        instance.save()
        return instance


class ApplicationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    review_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        action = validated_data.get('action')
        review_notes = validated_data.get('review_notes', '')
        
       
        
        with transaction.atomic():
            instance.reviewed_by = self.context['request'].user
            instance.reviewed_at = timezone.now()
            instance.review_notes = review_notes
            
            if action == 'approve':
                instance.status = 'approved'
                instance.save()
                
                # Queue background job
                create_parent_and_students_from_application_task(str(instance.id))
                
            else:
                instance.status = 'rejected'
                instance.rejection_reason = validated_data.get('rejection_reason', '')
                instance.save()
                
                # Send rejection email
                send_application_rejected_email_task(
                    instance.applicant.email,
                    instance.applicant.get_full_name(),
                    instance.rejection_reason
                )
        
        return instance