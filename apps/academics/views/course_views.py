# apps/academics/views/course_views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.academics.models import (
    Course, Subject, AcademicYear, Term,
    CourseMaterial, CourseAnnouncement, Enrollment
)
from apps.academics.serializers.course_serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateSerializer,
    CourseUpdateSerializer, CourseStatusUpdateSerializer, CourseSearchSerializer,
    SubjectSerializer, SubjectListSerializer, AcademicYearSerializer,
    TermSerializer, CourseMaterialSerializer, CourseAnnouncementSerializer
)
from apps.academics.serializers.enrollment_serializers import (
    EnrollmentListSerializer, EnrollmentCreateSerializer, EnrollmentBulkCreateSerializer,
    EnrollmentUpdateSerializer
)
from apps.accounts.permissions import (
    IsAdmin, IsTeacher, IsStaff, CanManageCourses, CanViewCourses,
    CanEnrollStudents, IsAdminOrTeacher, IsOwnerOrAdmin
)


@extend_schema_view(
    list=extend_schema(
        summary="List courses",
        description="Retrieve a paginated list of courses with filtering options.",
        tags=['Courses']
    ),
    retrieve=extend_schema(
        summary="Get course details",
        description="Retrieve detailed information about a specific course.",
        tags=['Courses']
    ),
    create=extend_schema(
        summary="Create course",
        description="Create a new course.",
        tags=['Courses']
    ),
    update=extend_schema(
        summary="Update course",
        description="Update all fields of an existing course.",
        tags=['Courses']
    ),
    partial_update=extend_schema(
        summary="Partially update course",
        description="Update specific fields of an existing course.",
        tags=['Courses']
    ),
    destroy=extend_schema(
        summary="Delete course",
        description="Delete a course (admin only).",
        tags=['Courses']
    )
)
class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses.
    
    Provides CRUD operations for courses with role-based permissions.
    Additional actions available:
    - `enrollments/`: Manage course enrollments
    - `materials/`: Manage course materials
    - `announcements/`: Manage course announcements
    - `students/`: List enrolled students
    - `update_status/`: Update course status
    """
    queryset = Course.objects.select_related(
        'subject', 'instructor__user', 'grade_level', 'academic_year', 'term'
    ).prefetch_related(
        'materials', 'announcements'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'level': ['exact', 'in'],
        'grade_level': ['exact'],
        'subject': ['exact'],
        'instructor': ['exact'],
        'academic_year': ['exact'],
        'term': ['exact'],
        'start_date': ['gte', 'lte'],
        'end_date': ['gte', 'lte'],
    }
    search_fields = ['title', 'code', 'description', 'subject__name']
    ordering_fields = ['title', 'code', 'start_date', 'end_date', 'current_students']
    ordering = ['title']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'create':
            return CourseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CourseUpdateSerializer
        elif self.action == 'update_status':
            return CourseStatusUpdateSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'bulk_create']:
            permission_classes = [IsAuthenticated, IsAdminOrTeacher]
        elif self.action in ['update', 'partial_update', 'update_status']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action in ['enroll', 'bulk_enroll']:
            permission_classes = [IsAuthenticated, CanEnrollStudents]
        elif self.action in ['materials', 'announcements']:
            permission_classes = [IsAuthenticated, CanManageCourses]
        else:
            permission_classes = [IsAuthenticated, CanViewCourses]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user and query parameters"""
        queryset = super().get_queryset()
        user = self.request.user

        # Apply search filters
        search_serializer = CourseSearchSerializer(data=self.request.query_params)
        if search_serializer.is_valid():
            data = search_serializer.validated_data
            
            if data.get('available_only'):
                queryset = queryset.filter(
                    current_students__lt=models.F('max_students'),
                    status='active'
                )

        # Role-based filtering
        if user.role == 'student' and hasattr(user, 'student_profile'):
            # Students see courses they're enrolled in and available courses
            enrolled_courses = Enrollment.objects.filter(
                student=user.student_profile
            ).values_list('course_id', flat=True)
            queryset = queryset.filter(
                Q(id__in=enrolled_courses) |
                Q(status='active', grade_level__isnull=False)
            )
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            # Teachers see courses they teach
            queryset = queryset.filter(instructor=user.teacher_profile)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            # Parents see courses their children are enrolled in
            children = user.parent_profile.children.all()
            queryset = queryset.filter(
                enrollments__student__in=children
            ).distinct()

        return queryset

    @extend_schema(
        summary="Get course enrollments",
        description="Retrieve all enrollments for a specific course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get course enrollments"""
        course = self.get_object()
        enrollments = course.enrollments.select_related('student__user').all()
        
        serializer = EnrollmentListSerializer(enrollments, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Enroll student in course",
        description="Enroll a student in this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll(self, request, pk=None):
        """Enroll a student in the course"""
        course = self.get_object()
        
        # Get student from request
        student_id = request.data.get('student_id')
        if not student_id:
            return Response(
                {"error": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create enrollment
        serializer = EnrollmentCreateSerializer(
            data={'student': student.id, 'course': course.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            enrollment = serializer.save()
            return Response(
                EnrollmentListSerializer(enrollment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Bulk enroll students",
        description="Enroll multiple students in this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['post'], url_path='bulk-enroll')
    def bulk_enroll(self, request, pk=None):
        """Bulk enroll students in the course"""
        course = self.get_object()
        
        data = {
            'course': course.id,
            'students': request.data.get('students', []),
            'status': request.data.get('status', 'enrolled')
        }
        
        serializer = EnrollmentBulkCreateSerializer(data=data)
        if serializer.is_valid():
            enrollments = serializer.save()
            return Response({
                'message': f'Successfully enrolled {len(enrollments)} students',
                'enrollments': EnrollmentListSerializer(
                    enrollments, many=True, context={'request': request}
                ).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get enrolled students",
        description="List all students enrolled in this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get enrolled students"""
        course = self.get_object()
        enrollments = course.enrollments.filter(status='enrolled')
        
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            students_data.append({
                'id': student.user.id,
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'email': student.user.email,
                'avatar': request.build_absolute_uri(student.user.profile_picture.url) if student.user.profile_picture else None,
                'enrollment_date': enrollment.enrollment_date,
                'progress': enrollment.progress,
                'final_grade': enrollment.final_grade
            })
        
        return Response(students_data)

    @extend_schema(
        summary="Update course status",
        description="Update the status of a course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update course status"""
        course = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            course.status = serializer.validated_data['status']
            course.save()
            
            return Response({
                'id': course.id,
                'status': course.status,
                'message': f'Course status updated to {course.status}'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get course materials",
        description="Retrieve all materials for this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['get', 'post'])
    def materials(self, request, pk=None):
        """Manage course materials"""
        course = self.get_object()
        
        if request.method == 'GET':
            materials = course.materials.all()
            serializer = CourseMaterialSerializer(materials, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = CourseMaterialSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(course=course, uploaded_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get course announcements",
        description="Retrieve all announcements for this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['get', 'post'])
    def announcements(self, request, pk=None):
        """Manage course announcements"""
        course = self.get_object()
        
        if request.method == 'GET':
            announcements = course.announcements.all()
            serializer = CourseAnnouncementSerializer(
                announcements, many=True, context={'request': request}
            )
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = CourseAnnouncementSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(course=course, author=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get course stats",
        description="Get statistics for this course.",
        tags=['Courses']
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get course statistics"""
        course = self.get_object()
        
        enrollments = course.enrollments.all()
        
        return Response({
            'total_enrollments': enrollments.count(),
            'enrolled': enrollments.filter(status='enrolled').count(),
            'completed': enrollments.filter(status='completed').count(),
            'dropped': enrollments.filter(status='dropped').count(),
            'waitlisted': enrollments.filter(status='waitlisted').count(),
            'pending': enrollments.filter(status='pending').count(),
            'available_seats': max(0, course.max_students - course.current_students),
            'avg_progress': enrollments.filter(status='enrolled').aggregate(
                avg_progress=models.Avg('progress')
            )['avg_progress'] or 0
        })


@extend_schema_view(
    list=extend_schema(tags=['Subjects']),
    retrieve=extend_schema(tags=['Subjects'])
)
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing subjects"""
    queryset = Subject.objects.filter(is_active=True)
    serializer_class = SubjectListSerializer
    permission_classes = [IsAuthenticated, CanViewCourses]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_islamic']
    search_fields = ['name', 'code']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubjectSerializer
        return SubjectListSerializer


@extend_schema_view(
    list=extend_schema(tags=['Academic Years']),
    retrieve=extend_schema(tags=['Academic Years'])
)
class AcademicYearViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing academic years"""
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated, CanViewCourses]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-start_date']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current academic year"""
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            serializer = self.get_serializer(current_year)
            return Response(serializer.data)
        return Response({"detail": "No current academic year found"}, status=404)


@extend_schema_view(
    list=extend_schema(tags=['Terms']),
    retrieve=extend_schema(tags=['Terms'])
)
class TermViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing terms"""
    queryset = Term.objects.all()
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated, CanViewCourses]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'term_type', 'is_current']
    ordering = ['start_date']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current term"""
        current_term = Term.objects.filter(is_current=True).first()
        if current_term:
            serializer = self.get_serializer(current_term)
            return Response(serializer.data)
        return Response({"detail": "No current term found"}, status=404)