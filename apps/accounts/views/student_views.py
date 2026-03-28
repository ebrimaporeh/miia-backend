# apps/accounts/views/student_views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db import models


from apps.accounts.models import Student, StudentDocument, StudentNote
from apps.accounts.serializers.student_serializers import (
    StudentListSerializer, StudentDetailSerializer, StudentCreateSerializer,
    StudentUpdateSerializer, StudentPerformanceUpdateSerializer, StudentEnrollmentSerializer,
    StudentBulkCreateSerializer, StudentSearchSerializer, StudentDocumentSerializer,
    StudentNoteSerializer
)
from apps.accounts.serializers.parent_serializers import ParentChildCreateSerializer
from apps.accounts.permissions import (
    IsAdmin, IsTeacher, IsStaff, CanViewStudents, CanManageStudents,
    CanViewStudentProgress, CanManageStudentDocuments, IsOwnerOrParentOrTeacherOrAdmin,
    CanMarkAttendance, CanViewAttendance
)


@extend_schema_view(
    list=extend_schema(
        summary="List students",
        description="Retrieve a paginated list of students with filtering options.",
        tags=['Students']
    ),
    retrieve=extend_schema(
        summary="Get student details",
        description="Retrieve detailed information about a specific student.",
        tags=['Students']
    ),
    create=extend_schema(
        summary="Create student",
        description="Create a new student with associated user account.",
        tags=['Students']
    ),
    update=extend_schema(
        summary="Update student",
        description="Update all fields of an existing student.",
        tags=['Students']
    ),
    partial_update=extend_schema(
        summary="Partially update student",
        description="Update specific fields of an existing student.",
        tags=['Students']
    ),
    destroy=extend_schema(
        summary="Delete student",
        description="Delete a student record (admin only).",
        tags=['Students']
    )
)
class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students.
    
    Provides CRUD operations for students with role-based permissions.
    Additional actions available:
    - `enrollments/`: List student's course enrollments
    - `attendance/`: Get student's attendance records
    - `grades/`: Get student's grades
    - `performance/`: Update student performance
    - `documents/`: Manage student documents
    - `notes/`: Manage student notes
    - `bulk_create/`: Bulk create students
    """
    queryset = Student.objects.select_related(
        'user', 'advisor__user'
    ).prefetch_related(
        'documents', 'student_notes'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'performance': ['exact', 'in'],
        'gender': ['exact'],
        'department': ['exact'],
        'enrollment_date': ['gte', 'lte', 'exact'],
        'advisor': ['exact'],
    }
    search_fields = [
        'student_id', 'user__first_name', 'user__last_name', 'user__email',
        'guardian_name', 'guardian_email', 'phone'
    ]
    ordering_fields = [
        'student_id', 'user__first_name', 'user__last_name', 
        'enrollment_date', 'status', 'performance'
    ]
    ordering = ['user__first_name', 'user__last_name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role"""
        if self.action == 'create':
            # Check if the user is a parent (adding their own child)
            if self.request.user.role == 'parent':
                return ParentChildCreateSerializer
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        elif self.action == 'list':
            return StudentListSerializer
        return StudentDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'bulk_create']:
            permission_classes = [IsAuthenticated, CanManageStudents]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanManageStudents]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action in ['documents', 'notes', 'performance']:
            permission_classes = [IsAuthenticated, CanViewStudentProgress]
        else:
            permission_classes = [IsAuthenticated, CanViewStudents]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Apply search filter from query params
        search_serializer = StudentSearchSerializer(data=self.request.query_params)
        if search_serializer.is_valid():
            data = search_serializer.validated_data
            
            if data.get('query'):
                queryset = queryset.filter(
                    models.Q(user__first_name__icontains=data['query']) |
                    models.Q(user__last_name__icontains=data['query']) |
                    models.Q(student_id__icontains=data['query']) |
                    models.Q(user__email__icontains=data['query'])
                )
            
            if data.get('status'):
                queryset = queryset.filter(status__in=data['status'])
            
            if data.get('performance'):
                queryset = queryset.filter(performance__in=data['performance'])
            
            if data.get('advisor'):
                queryset = queryset.filter(advisor__in=data['advisor'])
            
            if data.get('enrollment_date_from'):
                queryset = queryset.filter(enrollment_date__gte=data['enrollment_date_from'])
            
            if data.get('enrollment_date_to'):
                queryset = queryset.filter(enrollment_date__lte=data['enrollment_date_to'])
            
            if data.get('has_guardian'):
                queryset = queryset.exclude(guardian_email='')
            
            if data.get('has_medical_info'):
                queryset = queryset.filter(
                    models.Q(has_allergies=True) | 
                    models.Q(medical_conditions__isnull=False) & ~models.Q(medical_conditions='')
                )

        # Role-based filtering
        if user.role == 'student' and hasattr(user, 'student_profile'):
            queryset = queryset.filter(user=user)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            queryset = queryset.filter(parents=user.parent_profile)
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            # Teachers can see their advisees and students in their courses
            queryset = queryset.filter(
                models.Q(advisor=user.teacher_profile) |
                models.Q(enrollments__course__instructor=user.teacher_profile)
            ).distinct()

        return queryset

    @extend_schema(
        summary="Get student enrollments",
        description="Retrieve all course enrollments for a specific student.",
        responses={200: OpenApiTypes.OBJECT},
        tags=['Students']
    )
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get student's course enrollments"""
        student = self.get_object()
        enrollments = student.enrollments.select_related('course').all()
        
        from apps.academics.serializers import EnrollmentListSerializer
        serializer = EnrollmentListSerializer(enrollments, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Get student attendance",
        description="Retrieve attendance records for a specific student.",
        parameters=[
            OpenApiParameter(name='term', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='month', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
        ],
        tags=['Students']
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanViewAttendance])
    def attendance(self, request, pk=None):
        """Get student's attendance records"""
        student = self.get_object()
        # This will be implemented when attendance app is created
        return Response({
            'overall_rate': 95.5,
            'present': 38,
            'absent': 2,
            'late': 1,
            'excused': 1,
            'records': []
        })

    @extend_schema(
        summary="Get student grades",
        description="Retrieve grades for a specific student.",
        parameters=[
            OpenApiParameter(name='term', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='subject', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
        ],
        tags=['Students']
    )
    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        """Get student's grades"""
        student = self.get_object()
        # This will be implemented when grades app is created
        return Response({
            'gpa': 3.2,
            'courses': []
        })

    @extend_schema(
        summary="Update student performance",
        description="Update performance metrics for a student.",
        tags=['Students']
    )
    @action(detail=True, methods=['patch'])
    def performance(self, request, pk=None):
        """Update student performance"""
        student = self.get_object()
        serializer = self.get_serializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(StudentDetailSerializer(student, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Bulk create students",
        description="Create multiple students in a single request.",
        tags=['Students']
    )
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """Bulk create students"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'message': f'Successfully created {result["total_created"]} students',
                'created': StudentListSerializer(result['created'], many=True, context={'request': request}).data,
                'errors': result['errors']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Export students",
        description="Export student list in specified format.",
        parameters=[
            OpenApiParameter(name='format', type=OpenApiTypes.STR, 
                           enum=['csv', 'excel', 'pdf'], location=OpenApiParameter.QUERY),
        ],
        tags=['Students']
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export students to various formats"""
        queryset = self.filter_queryset(self.get_queryset())
        export_format = request.query_params.get('format', 'csv')
        
        # This would be implemented with export functionality
        return Response({'message': f'Export to {export_format} not implemented yet'})


@extend_schema_view(
    list=extend_schema(
        summary="List student documents",
        description="Retrieve all documents for a specific student.",
        tags=['Student Documents']
    ),
    create=extend_schema(
        summary="Upload document",
        description="Upload a new document for a student.",
        tags=['Student Documents']
    ),
    destroy=extend_schema(
        summary="Delete document",
        description="Delete a student document.",
        tags=['Student Documents']
    )
)
class StudentDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student documents"""
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated, CanManageStudentDocuments]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['document_type']
    search_fields = ['title']

    def get_queryset(self):
        """Filter documents by student"""
        student_id = self.kwargs.get('student_pk')
        if student_id:
            return StudentDocument.objects.filter(student_id=student_id)
        return StudentDocument.objects.none()

    def perform_create(self, serializer):
        """Set student and uploaded_by on creation"""
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'])
        serializer.save(student=student, uploaded_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List student notes",
        description="Retrieve all notes for a specific student.",
        tags=['Student Notes']
    ),
    create=extend_schema(
        summary="Create note",
        description="Create a new note for a student.",
        tags=['Student Notes']
    ),
    update=extend_schema(
        summary="Update note",
        description="Update an existing student note.",
        tags=['Student Notes']
    ),
    destroy=extend_schema(
        summary="Delete note",
        description="Delete a student note.",
        tags=['Student Notes']
    )
)
class StudentNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student notes"""
    serializer_class = StudentNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_private']

    def get_queryset(self):
        """Filter notes by student with privacy considerations"""
        student_id = self.kwargs.get('student_pk')
        if not student_id:
            return StudentNote.objects.none()

        queryset = StudentNote.objects.filter(student_id=student_id)
        user = self.request.user

        # Filter out private notes for non-authorized users
        if not (user.role in ['admin', 'teacher', 'staff']):
            queryset = queryset.filter(
                models.Q(is_private=False) | models.Q(author=user)
            )

        return queryset

    def perform_create(self, serializer):
        """Set student and author on creation"""
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'])
        serializer.save(student=student, author=self.request.user)

    def perform_update(self, serializer):
        """Ensure only author can update"""
        note = self.get_object()
        if note.author != self.request.user and not self.request.user.role == 'admin':
            self.permission_denied(self.request)
        serializer.save()