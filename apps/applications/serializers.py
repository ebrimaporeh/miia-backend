# apps/applications/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.applications.models import Application, ApplicantParent, ApplicantChild
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.accounts.models import Parent, Student
from django.utils import timezone

from apps.accounts.utils.student_utils import generate_student_id, generate_student_email

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
        
        if not instance.terms_accepted:
            raise serializers.ValidationError({"terms_accepted": "You must accept the terms and conditions."})
        
        if not instance.privacy_accepted:
            raise serializers.ValidationError({"privacy_accepted": "You must accept the privacy policy."})
        
        return attrs
    
    def update(self, instance, validated_data):
        instance.status = 'submitted'
        instance.current_step = 3
        instance.submitted_at = timezone.now()
        instance.save()
        return instance


class ApplicationReviewSerializer(serializers.Serializer):
    """Serializer for admin review"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    review_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        action = validated_data.get('action')
        review_notes = validated_data.get('review_notes', '')
        
       
        
        User = get_user_model()
        
        with transaction.atomic():
            instance.reviewed_by = self.context['request'].user
            instance.reviewed_at = timezone.now()
            instance.review_notes = review_notes
            
            if action == 'approve':
                instance.status = 'approved'
                self._create_parent_and_students(instance)
            else:
                instance.status = 'rejected'
                instance.rejection_reason = validated_data.get('rejection_reason', '')
            
            instance.save()
        
        return instance
    
    def _create_parent_and_students(self, application):
        """Create Parent and Student records from application data"""
        from django.contrib.auth import get_user_model
        from apps.accounts.models import Parent, Student
        from apps.accounts.utils.student_utils import generate_student_id, generate_student_email
        import secrets
        
        User = get_user_model()
        
        # Get the applicant parent data
        applicant_parent = application.applicant_parent
        
        # Generate a random password
        random_password = secrets.token_urlsafe(12)
        
        # Create User for parent (reuse applicant's email or use parent email)
        parent_user = User.objects.create_user(
            username=applicant_parent.email.split('@')[0],
            email=applicant_parent.email,
            password=random_password,
            first_name=applicant_parent.first_name,
            last_name=applicant_parent.last_name,
            role='parent',
            is_active=True
        )
        
        # Create Parent profile
        parent = Parent.objects.create(
            user=parent_user,
            relationship=applicant_parent.relationship,
            occupation=applicant_parent.occupation,
            phone=applicant_parent.phone,
            alternate_phone=applicant_parent.alternate_phone,
            address=applicant_parent.address
        )
        
        # Link to application
        application.parent = parent
        
        # Create Student records for each child
        created_students = []
        for child_data in application.applicant_children.all():
            # Create username from name
            username = f"{child_data.first_name.lower()}.{child_data.last_name.lower()}"
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create User for student
            student_user = User.objects.create_user(
                username=username,
                email=generate_student_email(child_data.first_name, child_data.last_name),
                password=secrets.token_urlsafe(12),
                first_name=child_data.first_name,
                last_name=child_data.last_name,
                role='student',
                is_active=True
            )
            
            # Create Student profile
            student = Student.objects.create(
                user=student_user,
                student_id=generate_student_id(),
                date_of_birth=child_data.date_of_birth,
                gender=child_data.gender,
                enrollment_date=timezone.now().date(),
                status='active',
                has_allergies=child_data.has_allergies,
                allergy_details=child_data.allergy_details,
                medical_conditions=child_data.medical_conditions,
                phone=child_data.phone,
                address=child_data.address or applicant_parent.address,
                guardian_name=applicant_parent.full_name,
                guardian_phone=applicant_parent.phone,
                guardian_email=applicant_parent.email,
                guardian_relationship=applicant_parent.relationship
            )
            
            # Link to parent
            parent.children.add(student)
            created_students.append(student)
        
        # Send email with credentials (will be implemented later)
        self._send_approval_email(parent_user, random_password, created_students)
    
    def _send_approval_email(self, user, password, students):
        """Placeholder for sending approval email"""
        # TODO: Implement email sending with background job
        pass