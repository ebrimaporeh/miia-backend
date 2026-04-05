# apps/applications/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.applications.models import Application, ApplicantParent, ApplicantChild
from apps.applications.serializers import (
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationParentUpdateSerializer,
    ApplicationChildCreateSerializer,
    ApplicationChildUpdateSerializer,
    ApplicationSubmitSerializer,
    ApplicationReviewSerializer,
)
from apps.accounts.permissions import IsAdmin, IsApplicant


@extend_schema_view(
    list=extend_schema(
        summary="List applications",
        description="Retrieve list of applications based on user role",
        tags=['Applications']
    ),
    retrieve=extend_schema(
        summary="Get application details",
        description="Retrieve detailed information about a specific application",
        tags=['Applications']
    ),
    create=extend_schema(
        summary="Create application",
        description="Create a new application for an applicant",
        tags=['Applications']
    ),
)
class ApplicationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing applications.
    
    Provides:
    - GET /api/applications/ - List applications (admin sees all, applicant sees own)
    - GET /api/applications/{id}/ - Get application details
    - POST /api/applications/ - Create new application
    - PATCH /api/applications/{id}/parent/ - Update parent information (Step 1)
    - POST /api/applications/{id}/children/ - Add a child (Step 2)
    - PATCH /api/applications/{id}/children/{child_id}/ - Update child
    - DELETE /api/applications/{id}/children/{child_id}/ - Remove child
    - POST /api/applications/{id}/submit/ - Submit application (Step 3)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['applicant__email', 'applicant__first_name', 'applicant__last_name']
    ordering_fields = ['created_at', 'submitted_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter applications based on user role"""
        user = self.request.user
        
        if user.is_authenticated and user.role == 'admin':
            return Application.objects.all().select_related('applicant', 'applicant_parent')
        
        if user.is_authenticated and user.role == 'applicant':
            return Application.objects.filter(applicant=user).select_related('applicant', 'applicant_parent')
        
        return Application.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'create':
            return ApplicationDetailSerializer
        elif self.action == 'parent':
            return ApplicationParentUpdateSerializer
        elif self.action == 'add_child':
            return ApplicationChildCreateSerializer
        elif self.action == 'update_child':
            return ApplicationChildUpdateSerializer
        elif self.action == 'submit':
            return ApplicationSubmitSerializer
        return ApplicationDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['parent', 'add_child', 'update_child', 'delete_child', 'submit']:
            permission_classes = [permissions.IsAuthenticated, IsApplicant]
        elif self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Create a new application for an applicant"""
        # Check if user already has an application
        if request.user.is_authenticated:
            existing_app = Application.objects.filter(applicant=request.user).first()
            if existing_app:
                serializer = self.get_serializer(existing_app)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new application
        application = Application.objects.create(
            applicant=request.user if request.user.is_authenticated else None,
            status='draft',
            current_step=1
        )
        
        serializer = self.get_serializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put', 'patch'], url_path='parent')
    def parent(self, request, pk=None):
        """Update parent/guardian information (Step 1)"""
        application = self.get_object()
        
        # Check if user owns this application
        if application.applicant != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create ApplicantParent
        applicant_parent, created = ApplicantParent.objects.get_or_create(
            application=application
        )
        
        serializer = self.get_serializer(applicant_parent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Update application step if needed
            if application.current_step == 1:
                application.current_step = 2
                application.save()
            
            # Return full application data
            app_serializer = ApplicationDetailSerializer(application, context={'request': request})
            return Response(app_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='children')
    def add_child(self, request, pk=None):
        """Add a child to the application (Step 2)"""
        application = self.get_object()
        
        # Check if user owns this application
        if application.applicant != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application is still editable
        if application.status not in ['draft', 'in_progress']:
            return Response(
                {'error': f'Cannot add children. Application is already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            child = serializer.save(application=application)
            
            # Update application step if needed
            if application.current_step == 2:
                application.current_step = 2
                application.save()
            
            # Return the created child data
            child_serializer = ApplicationChildUpdateSerializer(child)
            return Response(child_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put', 'patch'], url_path='children/(?P<child_id>[^/.]+)')
    def update_child(self, request, pk=None, child_id=None):
        """Update a child in the application"""
        application = self.get_object()
        
        # Check if user owns this application
        if application.applicant != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        child = get_object_or_404(ApplicantChild, id=child_id, application=application)
        
        serializer = self.get_serializer(child, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='children/(?P<child_id>[^/.]+)')
    def delete_child(self, request, pk=None, child_id=None):
        """Delete a child from the application"""
        application = self.get_object()
        
        # Check if user owns this application
        if application.applicant != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        child = get_object_or_404(ApplicantChild, id=child_id, application=application)
        child.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit the application for review (Step 3)"""
        application = self.get_object()
        
        # Check if user owns this application
        if application.applicant != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to submit this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already submitted
        if application.status not in ['draft', 'in_progress']:
            return Response(
                {'error': f'Application already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            application = serializer.save()
            return Response(
                ApplicationDetailSerializer(application, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my')
    def my_applications(self, request):
        """Get current user's applications"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        applications = Application.objects.filter(applicant=request.user).order_by('-created_at')
        serializer = ApplicationListSerializer(applications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='current')
    def current_application(self, request):
        """Get current user's active application"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        application = Application.objects.filter(
            applicant=request.user,
            status__in=['draft', 'in_progress', 'under_review', 'rejected', 'submitted']
        ).order_by('-created_at').first()
        
        if not application:
            return Response(
                {'message': 'No active application found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApplicationDetailSerializer(application, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List all applications",
        description="Retrieve all applications for admin review",
        tags=['Admin - Applications']
    ),
    retrieve=extend_schema(
        summary="Get application details",
        description="Retrieve detailed application information for admin",
        tags=['Admin - Applications']
    ),
    review=extend_schema(
        summary="Review application",
        description="Approve or reject an application",
        tags=['Admin - Applications']
    ),
    stats=extend_schema(
        summary="Get application statistics",
        description="Get statistics about applications",
        tags=['Admin - Applications']
    )
)
class AdminApplicationViewSet(viewsets.GenericViewSet):
    """
    Admin-only ViewSet for managing applications.
    
    Provides:
    - GET /api/admin/applications/ - List all applications with filters
    - GET /api/admin/applications/{id}/ - Get application details
    - POST /api/admin/applications/{id}/review/ - Approve or reject
    - GET /api/admin/applications/stats/ - Get statistics
    """
    
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Application.objects.all().select_related(
        'applicant', 'applicant_parent'
    ).prefetch_related('applicant_children')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = [
        'applicant__email', 'applicant__first_name', 'applicant__last_name',
        'applicant_parent__full_name', 'applicant_parent__email'
    ]
    ordering_fields = ['created_at', 'submitted_at', 'status']
    ordering = ['-submitted_at', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'review':
            return ApplicationReviewSerializer
        return ApplicationDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List all applications with counts for dashboard"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Counts for dashboard
        counts = {
            'pending_review': Application.objects.filter(status='submitted').count(),
            'under_review': Application.objects.filter(status='under_review').count(),
            'approved': Application.objects.filter(status='approved').count(),
            'rejected': Application.objects.filter(status='rejected').count(),
            'draft': Application.objects.filter(status='draft').count(),
            'in_progress': Application.objects.filter(status='in_progress').count(),
            'total': Application.objects.count()
        }
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'counts': counts,
                'results': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'counts': counts,
            'results': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get application details for admin"""
        application = self.get_object()
        serializer = ApplicationDetailSerializer(application, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Approve or reject an application"""
        application = self.get_object()
        
        # Check if already reviewed
        if application.status in ['approved', 'rejected']:
            return Response(
                {'error': f'Application already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            application,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            return Response(
                ApplicationDetailSerializer(application, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='mark-under-review')
    def mark_under_review(self, request, pk=None):
        """Mark an application as under review"""
        application = self.get_object()
        
        if application.status != 'submitted':
            return Response(
                {'error': f'Cannot mark application as under review. Current status: {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'under_review'
        application.save()
        
        return Response({
            'message': 'Application marked as under review',
            'status': application.status
        })
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get application statistics"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Overall counts
        total = Application.objects.count()
        submitted = Application.objects.filter(status='submitted').count()
        under_review = Application.objects.filter(status='under_review').count()
        approved = Application.objects.filter(status='approved').count()
        rejected = Application.objects.filter(status='rejected').count()
        
        # Applications this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = Application.objects.filter(created_at__gte=start_of_month).count()
        
        # Applications last 7 days
        last_7_days = Application.objects.filter(
            created_at__gte=now - timedelta(days=7)
        ).count()
        
        # Average review time (for reviewed applications)
        reviewed_apps = Application.objects.exclude(reviewed_at=None).exclude(submitted_at=None)
        avg_review_days = 0
        if reviewed_apps.exists():
            total_days = sum(
                (app.reviewed_at - app.submitted_at).days
                for app in reviewed_apps
            )
            avg_review_days = total_days / reviewed_apps.count()
        
        return Response({
            'total': total,
            'submitted': submitted,
            'under_review': under_review,
            'approved': approved,
            'rejected': rejected,
            'this_month': this_month,
            'last_7_days': last_7_days,
            'average_review_days': round(avg_review_days, 1),
            'completion_rate': round((approved + rejected) / total * 100, 1) if total > 0 else 0
        })
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Bulk update application statuses"""
        application_ids = request.data.get('application_ids', [])
        new_status = request.data.get('status')
        
        if not application_ids or not new_status:
            return Response(
                {'error': 'application_ids and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in ['under_review', 'approved', 'rejected']:
            return Response(
                {'error': 'Invalid status. Must be under_review, approved, or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        applications = Application.objects.filter(id__in=application_ids)
        count = applications.count()
        
        applications.update(status=new_status)
        
        return Response({
            'message': f'Updated {count} applications to {new_status}',
            'updated_count': count
        })