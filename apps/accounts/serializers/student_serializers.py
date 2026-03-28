# apps/accounts/serializers/student_serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.accounts.models import Student, GradeLevel, StudentDocument, StudentNote
from apps.accounts.serializers.auth_serializers import UserProfileSerializer, UserUpdateSerializer
from apps.accounts.utils.student_utils import (
    create_student,
    generate_student_email,
    generate_student_id,
    reset_student_password
)
from django.db import transaction


User = get_user_model()

class GradeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeLevel
        fields = ['id', 'name', 'level_number', 'display_name', 'min_age', 'max_age', 'is_active', 'order']


class StudentDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentDocument
        fields = ['id', 'student', 'document_type', 'title', 'file', 'file_url', 
                  'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate(self, attrs):
        """Ensure student is provided in context for creation"""
        if self.context.get('request') and self.context['request'].method == 'POST':
            # If student is not in attrs, try to get from view context
            if 'student' not in attrs:
                view = self.context.get('view')
                if view and hasattr(view, 'kwargs') and 'student_pk' in view.kwargs:
                    try:
                        student = Student.objects.get(pk=view.kwargs['student_pk'])
                        attrs['student'] = student
                    except Student.DoesNotExist:
                        raise serializers.ValidationError({"student": "Student not found"})
                else:
                    raise serializers.ValidationError({"student": "Student is required"})
            
            # Set uploaded_by to current user
            attrs['uploaded_by'] = self.context['request'].user
        
        return attrs


class StudentNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = StudentNote
        fields = ['id', 'student', 'author', 'author_name', 'content', 'is_private', 
                  'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        if self.context.get('request') and self.context['request'].method == 'POST':
            # If student is not in attrs, try to get from view context
            if 'student' not in attrs:
                view = self.context.get('view')
                if view and hasattr(view, 'kwargs') and 'student_pk' in view.kwargs:
                    try:
                        student = Student.objects.get(pk=view.kwargs['student_pk'])
                        attrs['student'] = student
                    except Student.DoesNotExist:
                        raise serializers.ValidationError({"student": "Student not found"})
                else:
                    raise serializers.ValidationError({"student": "Student is required"})
            
            # Set author to current user
            attrs['author'] = self.context['request'].user
        
        return attrs


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    id = serializers.UUIDField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    avatar = serializers.SerializerMethodField()
    # Comment out grade_level references until model is updated
    # grade_level_name = serializers.CharField(source='current_grade.name', read_only=True, default=None)
    advisor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'name', 'email', 'avatar', 'gender', 
            'status', 'performance', 'enrollment_date', 'advisor_name',
            'guardian_name', 'guardian_phone', 'guardian_email'
        ]
    
    def get_avatar(self, obj):
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
        return None
    
    def get_advisor_name(self, obj):
        if obj.advisor:
            return obj.advisor.user.get_full_name()
        return None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single student view"""
    user = UserProfileSerializer(read_only=True)
    id = serializers.UUIDField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)
    
    # Comment out grade level references until model is updated
    # current_grade_detail = GradeLevelSerializer(source='current_grade', read_only=True)
    
    # Nested objects with filtering options
    documents = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    
    # Advisor detail
    advisor_detail = serializers.SerializerMethodField()
    
    # Computed fields (placeholder implementations)
    enrolled_courses_count = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    average_grade = serializers.SerializerMethodField()
    gpa = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'student_id', 'name', 'email', 'username', 'avatar',
            'date_of_birth', 'age', 'gender', 'enrollment_date', 'graduation_date',
            'status', 'performance', 'department', 'advisor', 'advisor_detail',
            'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'phone', 'address', 'has_allergies', 'allergy_details', 'medical_conditions',
            'last_active', 'notes', 'documents', 
            'enrolled_courses_count', 'attendance_rate', 'average_grade', 'gpa',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_active']
    
    def get_avatar(self, obj):
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
        return None
    
    def get_advisor_detail(self, obj):
        if obj.advisor:
            return {
                'id': obj.advisor.user.id,
                'employee_id': obj.advisor.employee_id,
                'name': obj.advisor.user.get_full_name(),
                'email': obj.advisor.user.email,
                'qualification': obj.advisor.qualification,
                'specialization': obj.advisor.specialization
            }
        return None
    
    def get_documents(self, obj):
        """Get documents with optional type filtering"""
        request = self.context.get('request')
        documents = obj.documents.all()
        
        # Filter by document type if specified
        if request and request.query_params.get('document_type'):
            documents = documents.filter(document_type=request.query_params['document_type'])
        
        # Limit number of documents returned
        if request and request.query_params.get('limit_documents'):
            try:
                limit = int(request.query_params['limit_documents'])
                documents = documents[:limit]
            except (ValueError, TypeError):
                pass
        
        serializer = StudentDocumentSerializer(documents, many=True, context=self.context)
        return serializer.data
    
    def get_notes(self, obj):
        """Get notes with privacy filtering"""
        request = self.context.get('request')
        if not request:
            return []
        
        notes = obj.student_notes.all()
        user = request.user
        
        # Filter out private notes if user is not authorized
        if not (user.role in ['admin', 'teacher', 'staff'] or 
                (hasattr(user, 'student_profile') and user.student_profile == obj)):
            notes = notes.filter(is_private=False)
        
        # Limit number of notes returned
        if request.query_params.get('limit_notes'):
            try:
                limit = int(request.query_params['limit_notes'])
                notes = notes[:limit]
            except (ValueError, TypeError):
                pass
        
        serializer = StudentNoteSerializer(notes, many=True, context=self.context)
        return serializer.data
    
    # Placeholder methods for computed fields
    def get_enrolled_courses_count(self, obj):
        """Placeholder - will be implemented when academics app is created"""
        return 0
    
    def get_attendance_rate(self, obj):
        """Placeholder - will be implemented with attendance app"""
        return 95.5  # Example value
    
    def get_average_grade(self, obj):
        """Placeholder - will be implemented with grades app"""
        return 85.0  # Example value
    
    def get_gpa(self, obj):
        """Placeholder - will be implemented with grades app"""
        return 3.2  # Example value


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new student with user account (admin/teacher only)"""
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    send_invitation = serializers.BooleanField(write_only=True, required=False, default=False)
    
    # Output fields
    id = serializers.UUIDField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email_display = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            # Input fields
            'email', 'first_name', 'last_name', 'password', 'confirm_password',
            'date_of_birth', 'gender', 'graduation_date',
            'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'phone', 'address', 'advisor', 'department', 'status', 'performance',
            'has_allergies', 'allergy_details', 'medical_conditions', 'notes',
            'send_invitation',
            # Output fields
            'id', 'full_name', 'email_display', 'student_id'
        ]
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('context', {}).get('request', None)
        super().__init__(*args, **kwargs)
    
    def validate(self, data):
        """Validate email uniqueness and password match"""
        email = data.get('email', '')
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # If email is provided, check if it already exists
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        # Validate password if provided
        if password:
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
            if len(password) < 8:
                raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract user data
        email = validated_data.pop('email', None)
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password', None)
        send_invitation = validated_data.pop('send_invitation', False)
        
        # Determine who is creating the student
        is_parent = self.request and self.request.user.role == 'parent'
        
        # Parents shouldn't use this serializer
        if is_parent:
            raise serializers.ValidationError("Parents should use the parent student creation endpoint.")
        
        # Create student using utility
        student = create_student(
            first_name=first_name,
            last_name=last_name,
            email=email,  # Will be auto-generated if not provided
            password=password,  # Will use default if not provided
            is_active=True,  # Students created by admin/teacher are active
            **validated_data
        )
        
        # Send invitation email if requested
        if send_invitation:
            self._send_invitation_email(student, password or Student.STUDENT_DEFAULT_PASSWORD)
        
        return student
    
    def _send_invitation_email(self, student, password):
        """Placeholder for sending invitation email"""
        # This would be implemented with your email service
        pass


class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing student"""
    
    # Use UserUpdateSerializer for user fields (not read-only)
    user = UserUpdateSerializer(required=False)
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'date_of_birth', 'gender', 'enrollment_date', 'graduation_date',
            'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'phone', 'address', 'advisor', 'department', 'status', 'performance',
            'has_allergies', 'allergy_details', 'medical_conditions', 'notes',
            'user'  
        ]
    
    def validate_student_id(self, value):
        """Validate student_id uniqueness if changed"""
        if self.instance and self.instance.student_id != value:
            if Student.objects.filter(student_id=value).exists():
                raise serializers.ValidationError("Student with this ID already exists.")
        return value
    
    def update(self, instance, validated_data):
        # Extract user data if present
        user_data = validated_data.pop('user', None)
        
        # Update user if user_data provided
        if user_data:
            user_serializer = UserUpdateSerializer(
                instance=instance.user,
                data=user_data,
                partial=True,
                context=self.context
            )
            if user_serializer.is_valid(raise_exception=True):
                user_serializer.save()
        
        # Update student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class StudentBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating students"""
    students = StudentCreateSerializer(many=True)
    skip_duplicates = serializers.BooleanField(default=False)
    
    def create(self, validated_data):
        students_data = validated_data.get('students', [])
        skip_duplicates = validated_data.get('skip_duplicates', False)
        
        created_students = []
        errors = []
        
        for index, student_data in enumerate(students_data):
            try:
                # Check for duplicate email
                email = student_data.get('email')
                if User.objects.filter(email=email).exists():
                    if skip_duplicates:
                        continue
                    else:
                        errors.append({
                            'index': index,
                            'email': email,
                            'error': 'Email already exists'
                        })
                        continue
                
                # Create student
                serializer = StudentCreateSerializer(data=student_data)
                if serializer.is_valid():
                    student = serializer.save()
                    created_students.append(student)
                else:
                    errors.append({
                        'index': index,
                        'email': email,
                        'errors': serializer.errors
                    })
                    
            except Exception as e:
                errors.append({
                    'index': index,
                    'error': str(e)
                })
        
        return {
            'created': created_students,
            'errors': errors,
            'total_created': len(created_students),
            'total_errors': len(errors)
        }


class StudentPerformanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating just performance-related fields"""
    class Meta:
        model = Student
        fields = ['performance', 'status', 'advisor', 'notes']


class StudentEnrollmentSerializer(serializers.Serializer):
    """Serializer for enrollment operations"""
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=['enroll', 'withdraw', 'suspend', 'activate'])
    reason = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False)


class StudentSearchSerializer(serializers.Serializer):
    """Serializer for student search/filter parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    status = serializers.MultipleChoiceField(
        choices=Student.STATUS_CHOICES,
        required=False
    )
    performance = serializers.MultipleChoiceField(
        choices=Student.PERFORMANCE_CHOICES,
        required=False
    )
    grade_level = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    advisor = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    enrollment_date_from = serializers.DateField(required=False)
    enrollment_date_to = serializers.DateField(required=False)
    has_guardian = serializers.BooleanField(required=False)
    has_medical_info = serializers.BooleanField(required=False)