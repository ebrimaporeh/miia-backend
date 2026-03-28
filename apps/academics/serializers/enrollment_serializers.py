# apps/academics/serializers/enrollment_serializers.py
from rest_framework import serializers
from django.db import transaction
from apps.academics.models import Enrollment, Course
from apps.accounts.models import Student


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Serializer for enrollment list views"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    student_avatar = serializers.SerializerMethodField()
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_instructor = serializers.CharField(source='course.instructor.user.get_full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_id', 'student_avatar',
            'course', 'course_code', 'course_title', 'course_instructor',
            'enrollment_date', 'status', 'progress', 'last_activity',
            'final_grade', 'final_score'
        ]
    
    def get_student_avatar(self, obj):
        if obj.student.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.student.user.profile_picture.url)
        return None


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for enrollment"""
    student_detail = serializers.SerializerMethodField()
    course_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = '__all__'
    
    def get_student_detail(self, obj):
        from apps.accounts.serializers.student_serializers import StudentListSerializer
        return StudentListSerializer(obj.student, context=self.context).data
    
    def get_course_detail(self, obj):
        from .course_serializers import CourseListSerializer
        return CourseListSerializer(obj.course, context=self.context).data


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating enrollments"""
    
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'status']
    
    def validate(self, data):
        """Validate enrollment conditions"""
        student = data['student']
        course = data['course']
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError("Student is already enrolled in this course.")
        
        # Check course capacity
        if course.current_students >= course.max_students:
            if data.get('status') != 'waitlisted':
                raise serializers.ValidationError("Course is full. Please use 'waitlisted' status.")
        
        # Check grade level
        if student.current_grade and course.grade_level:
            if student.current_grade.level_number != course.grade_level.level_number:
                raise serializers.ValidationError(
                    f"Student grade level ({student.current_grade.name}) does not match "
                    f"course grade level ({course.grade_level.name})."
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        course = validated_data['course']
        enrollment = Enrollment.objects.create(**validated_data)
        
        # Update course student count if status is 'enrolled'
        if enrollment.status == 'enrolled':
            course.current_students += 1
            course.save()
        
        return enrollment


class EnrollmentBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk enrollment creation"""
    course = serializers.UUIDField()
    students = serializers.ListField(child=serializers.UUIDField())
    status = serializers.ChoiceField(choices=Enrollment.STATUS_CHOICES, default='enrolled')
    
    def validate(self, data):
        """Validate bulk enrollment"""
        try:
            course = Course.objects.get(pk=data['course'])
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course": "Course not found."})
        
        students = Student.objects.filter(pk__in=data['students'])
        if len(students) != len(data['students']):
            raise serializers.ValidationError({"students": "One or more students not found."})
        
        # Check capacity
        if data['status'] == 'enrolled':
            available_slots = course.max_students - course.current_students
            if len(data['students']) > available_slots:
                raise serializers.ValidationError(
                    f"Not enough available slots. Available: {available_slots}, Requested: {len(data['students'])}"
                )
        
        data['course'] = course
        data['student_objects'] = students
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        course = validated_data['course']
        students = validated_data['student_objects']
        status = validated_data['status']
        
        enrollments = []
        for student in students:
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'status': status}
            )
            if created:
                enrollments.append(enrollment)
        
        # Update course student count
        if status == 'enrolled':
            course.current_students += len([e for e in enrollments if e.status == 'enrolled'])
            course.save()
        
        return enrollments


class EnrollmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating enrollment status"""
    
    class Meta:
        model = Enrollment
        fields = ['status', 'progress', 'final_grade', 'final_score']
    
    @transaction.atomic
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Update course student count if status changes
        if old_status != new_status:
            course = instance.course
            if old_status == 'enrolled' and new_status != 'enrolled':
                course.current_students = max(0, course.current_students - 1)
                course.save()
            elif old_status != 'enrolled' and new_status == 'enrolled':
                if course.current_students >= course.max_students:
                    raise serializers.ValidationError("Course is full.")
                course.current_students += 1
                course.save()
        
        return super().update(instance, validated_data)


class EnrollmentGradeUpdateSerializer(serializers.Serializer):
    """Serializer for bulk grade updates"""
    grades = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_grades(self, value):
        """Validate grade data"""
        for item in value:
            if 'enrollment_id' not in item:
                raise serializers.ValidationError("Each grade must include enrollment_id")
        return value


class EnrollmentSearchSerializer(serializers.Serializer):
    """Serializer for enrollment search/filter"""
    course = serializers.UUIDField(required=False)
    student = serializers.UUIDField(required=False)
    status = serializers.ListField(
        child=serializers.ChoiceField(choices=Enrollment.STATUS_CHOICES),
        required=False
    )
    enrollment_date_from = serializers.DateField(required=False)
    enrollment_date_to = serializers.DateField(required=False)