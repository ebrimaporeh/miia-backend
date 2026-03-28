# apps/academics/serializers/course_serializers.py
from rest_framework import serializers
from django.db import transaction
from apps.academics.models import (
    Course, Subject, AcademicYear, Term, 
    CourseMaterial, CourseAnnouncement, Enrollment
)
from apps.accounts.models import Teacher, GradeLevel, Student
from apps.accounts.serializers.auth_serializers import UserProfileSerializer


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""
    class Meta:
        model = Subject
        fields = '__all__'


class SubjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for subject list views"""
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'category', 'is_islamic', 'is_active']


class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for AcademicYear model"""
    class Meta:
        model = AcademicYear
        fields = '__all__'


class TermSerializer(serializers.ModelSerializer):
    """Serializer for Term model"""
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    
    class Meta:
        model = Term
        fields = '__all__'


class TeacherBasicSerializer(serializers.Serializer):
    """Basic teacher info for course serializers"""
    id = serializers.UUIDField(source='user.id')
    name = serializers.CharField(source='user.get_full_name')
    email = serializers.EmailField(source='user.email')
    employee_id = serializers.CharField()


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for course list views"""
    instructor_name = serializers.CharField(source='instructor.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_level_name = serializers.CharField(source='grade_level.display_name', read_only=True)
    students_count = serializers.IntegerField(source='current_students', read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'code', 'description', 'instructor', 'instructor_name',
            'subject', 'subject_name', 'grade_level', 'grade_level_name',
            'credits', 'level', 'schedule', 'room', 'max_students', 'students_count',
            'start_date', 'end_date', 'status', 'color', 'enrollment_status'
        ]
    
    def get_enrollment_status(self, obj):
        """Get enrollment status for current user if student"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'student' and hasattr(request.user, 'student_profile'):
                try:
                    enrollment = Enrollment.objects.get(
                        student=request.user.student_profile,
                        course=obj
                    )
                    return enrollment.status
                except Enrollment.DoesNotExist:
                    return None
        return None


class CourseMaterialSerializer(serializers.ModelSerializer):
    """Serializer for CourseMaterial model"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseMaterial
        fields = [
            'id', 'course', 'name', 'type', 'file', 'file_url', 'url',
            'size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate(self, attrs):
        """Validate that either file or url is provided"""
        if not attrs.get('file') and not attrs.get('url'):
            raise serializers.ValidationError("Either file or url must be provided.")
        return attrs


class CourseAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for CourseAnnouncement model"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = CourseAnnouncement
        fields = [
            'id', 'course', 'title', 'content', 'author', 'author_name',
            'priority', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single course view"""
    instructor_detail = serializers.SerializerMethodField()
    subject_detail = SubjectSerializer(source='subject', read_only=True)
    grade_level_detail = serializers.SerializerMethodField()
    academic_year_detail = AcademicYearSerializer(source='academic_year', read_only=True)
    term_detail = TermSerializer(source='term', read_only=True)
    materials = CourseMaterialSerializer(many=True, read_only=True)
    announcements = serializers.SerializerMethodField()
    students_count = serializers.IntegerField(source='current_students', read_only=True)
    available_seats = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = '__all__'
    
    def get_instructor_detail(self, obj):
        if obj.instructor:
            return {
                'id': obj.instructor.user.id,
                'name': obj.instructor.user.get_full_name(),
                'email': obj.instructor.user.email,
                'employee_id': obj.instructor.employee_id,
                'qualification': obj.instructor.qualification,
                'specialization': obj.instructor.specialization
            }
        return None
    
    def get_grade_level_detail(self, obj):
        if obj.grade_level:
            return {
                'id': obj.grade_level.id,
                'name': obj.grade_level.name,
                'display_name': obj.grade_level.display_name,
                'level_number': obj.grade_level.level_number
            }
        return None
    
    def get_announcements(self, obj):
        """Get recent announcements with optional limit"""
        request = self.context.get('request')
        announcements = obj.announcements.all()
        
        if request and request.query_params.get('limit_announcements'):
            try:
                limit = int(request.query_params['limit_announcements'])
                announcements = announcements[:limit]
            except (ValueError, TypeError):
                pass
        
        return CourseAnnouncementSerializer(announcements, many=True, context=self.context).data
    
    def get_available_seats(self, obj):
        return max(0, obj.max_students - obj.current_students)
    
    def get_enrollment_status(self, obj):
        """Get enrollment status for current user if student"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'student' and hasattr(request.user, 'student_profile'):
                try:
                    enrollment = Enrollment.objects.get(
                        student=request.user.student_profile,
                        course=obj
                    )
                    return {
                        'status': enrollment.status,
                        'enrollment_date': enrollment.enrollment_date,
                        'progress': enrollment.progress,
                        'final_grade': enrollment.final_grade
                    }
                except Enrollment.DoesNotExist:
                    return None
        return None


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new course"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'code', 'description', 'subject', 'instructor',
            'grade_level', 'credits', 'level', 'schedule', 'duration',
            'room', 'max_students', 'start_date', 'end_date',
            'academic_year', 'term', 'prerequisites', 'objectives',
            'status', 'color'
        ]
    
    def validate_code(self, value):
        """Ensure course code is unique"""
        if Course.objects.filter(code=value).exists():
            raise serializers.ValidationError("Course with this code already exists.")
        return value
    
    def validate(self, data):
        """Validate dates and capacity"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date.")
        
        if data.get('max_students', 0) < 1:
            raise serializers.ValidationError({"max_students": "Maximum students must be at least 1."})
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        course = Course.objects.create(**validated_data)
        return course


class CourseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing course"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'instructor', 'credits', 'level',
            'schedule', 'duration', 'room', 'max_students', 'start_date',
            'end_date', 'academic_year', 'term', 'prerequisites',
            'objectives', 'status', 'color'
        ]
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date.")
        return data


class CourseStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating course status"""
    status = serializers.ChoiceField(choices=Course.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)


class CourseSearchSerializer(serializers.Serializer):
    """Serializer for course search/filter parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.ListField(child=serializers.UUIDField(), required=False)
    grade_level = serializers.ListField(child=serializers.UUIDField(), required=False)
    instructor = serializers.ListField(child=serializers.UUIDField(), required=False)
    status = serializers.ListField(
        child=serializers.ChoiceField(choices=Course.STATUS_CHOICES),
        required=False
    )
    level = serializers.ListField(
        child=serializers.ChoiceField(choices=Course.LEVEL_CHOICES),
        required=False
    )
    academic_year = serializers.UUIDField(required=False)
    term = serializers.UUIDField(required=False)
    available_only = serializers.BooleanField(required=False, default=False)