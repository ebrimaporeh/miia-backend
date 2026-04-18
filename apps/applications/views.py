# apps/applications/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from apps.core.pagination import CustomPageNumberPagination

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
        summary="List my applications",
        description="Retrieve all applications for the current applicant",
        tags=['Applications']
    ),
    create=extend_schema(
        summary="Create new application",
        description="Create a new application for the current user",
        tags=['Applications']
    ),
    retrieve=extend_schema(
        summary="Get application details",
        description="Retrieve detailed information about a specific application",
        tags=['Applications']
    ),
    update=extend_schema(
        summary="Update application",
        description="Update an existing application",
        tags=['Applications']
    ),
    partial_update=extend_schema(
        summary="Partially update application",
        description="Partially update an existing application",
        tags=['Applications']
    ),
    destroy=extend_schema(
        summary="Delete application",
        description="Delete an application (draft only)",
        tags=['Applications']
    ),
)
class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for applicants to manage their own applications.
    
    URL Structure:
    - GET    /api/applications/           - List my applications
    - POST   /api/applications/           - Create new application
    - GET    /api/applications/{id}/      - Get application details
    - PUT    /api/applications/{id}/      - Update application
    - PATCH  /api/applications/{id}/      - Partially update application
    - DELETE /api/applications/{id}/      - Delete draft application
    - PUT    /api/applications/{id}/parent/ - Update parent information (Step 1)
    - POST   /api/applications/{id}/children/ - Add a child (Step 2)
    - PUT    /api/applications/{id}/children/{child_id}/ - Update child
    - DELETE /api/applications/{id}/children/{child_id}/ - Remove child
    - POST   /api/applications/{id}/submit/ - Submit application (Step 3)
    - GET    /api/applications/current/   - Get current active application
    """
    
    # permission_classes = [permissions.IsAuthenticated, IsApplicant]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['applicant__email', 'applicant__first_name', 'applicant__last_name']
    ordering_fields = ['created_at', 'submitted_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only the current user's applications"""
        return Application.objects.filter(applicant=self.request.user).select_related(
            'applicant', 'applicant_parent'
        ).prefetch_related('applicant_children')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        serializer_map = {
            'list': ApplicationListSerializer,
            'create': ApplicationDetailSerializer,
            'retrieve': ApplicationDetailSerializer,
            'update': ApplicationDetailSerializer,
            'partial_update': ApplicationDetailSerializer,
            'parent': ApplicationParentUpdateSerializer,
            'add_child': ApplicationChildCreateSerializer,
            'update_child': ApplicationChildUpdateSerializer,
            'submit': ApplicationSubmitSerializer,
        }
        return serializer_map.get(self.action, ApplicationDetailSerializer)
    
    def create(self, request, *args, **kwargs):
        """Create a new application for the current user"""
        # Check if user already has a draft or in-progress application
        existing_app = Application.objects.filter(
            applicant=request.user,
            status__in=['draft', 'in_progress']
        ).first()
        
        if existing_app:
            serializer = self.get_serializer(existing_app)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new application
        application = Application.objects.create(
            applicant=request.user,
            status='draft',
            current_step=1
        )
        
        serializer = self.get_serializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update application (only allowed for draft/in_progress)"""
        application = self.get_object()
        
        if application.status not in ['draft', 'in_progress']:
            return Response(
                {'error': f'Cannot update application. Current status: {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete application (only allowed for draft)"""
        application = self.get_object()
        
        if application.status != 'draft':
            return Response(
                {'error': f'Cannot delete application. Current status: {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update parent/guardian information",
        description="Update parent/guardian information for the application (Step 1 of 3)",
        tags=['Applications']
    )
    @action(detail=True, methods=['put', 'patch'], url_path='parent')
    def parent(self, request, pk=None):
        """Update parent/guardian information (Step 1)"""
        application = self.get_object()
        
        # Get or create ApplicantParent
        applicant_parent, created = ApplicantParent.objects.get_or_create(
            application=application
        )
        
        serializer = ApplicationParentUpdateSerializer(
            applicant_parent, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Update application step if moving forward
            if application.current_step == 1:
                application.current_step = 2
                application.save()
            
            # Return full application data
            app_serializer = ApplicationDetailSerializer(
                application, 
                context={'request': request}
            )
            return Response(app_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Add a child to application",
        description="Add a child to the application (Step 2 of 3)",
        tags=['Applications']
    )
    @action(detail=True, methods=['post'], url_path='children')
    def add_child(self, request, pk=None):
        """Add a child to the application (Step 2)"""
        application = self.get_object()
        
        # Check if application is still editable
        if application.status not in ['draft', 'in_progress']:
            return Response(
                {'error': f'Cannot add children. Application is already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ApplicationChildCreateSerializer(data=request.data)
        if serializer.is_valid():
            child = serializer.save(application=application)
            
            # Update application step if needed
            if application.current_step == 2:
                application.current_step = 2  # Stay on step 2 to add more children
                application.save()
            
            # Return the created child data
            child_serializer = ApplicationChildUpdateSerializer(child)
            return Response(child_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Update a child",
        description="Update a child's information in the application",
        tags=['Applications']
    )
    @action(detail=True, methods=['put', 'patch'], url_path='children/(?P<child_id>[^/.]+)')
    def update_child(self, request, pk=None, child_id=None):
        """Update a child in the application"""
        application = self.get_object()
        child = get_object_or_404(ApplicantChild, id=child_id, application=application)
        
        serializer = ApplicationChildUpdateSerializer(
            child, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Remove a child",
        description="Remove a child from the application",
        tags=['Applications']
    )
    @action(detail=True, methods=['delete'], url_path='children/(?P<child_id>[^/.]+)')
    def delete_child(self, request, pk=None, child_id=None):
        """Delete a child from the application"""
        application = self.get_object()
        child = get_object_or_404(ApplicantChild, id=child_id, application=application)
        child.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="Submit application for review",
        description="Submit the completed application for admin review (Step 3 of 3)",
        tags=['Applications']
    )
    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit the application for review (Step 3)"""
        application = self.get_object()
        
        # Check if already submitted
        if application.status not in ['draft', 'in_progress']:
            return Response(
                {'error': f'Application already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that required data is present
        if not hasattr(application, 'applicant_parent') or not application.applicant_parent:
            return Response(
                {'error': 'Parent/guardian information is required before submission.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if application.applicant_children.count() == 0:
            return Response(
                {'error': 'At least one child must be added before submission.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ApplicationSubmitSerializer(
            application, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            application = serializer.save()
            return Response(
                ApplicationDetailSerializer(application, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Get current active application",
        description="Get the current user's active application (draft or in progress)",
        tags=['Applications']
    )
    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """Get current user's active application"""
        application = Application.objects.filter(
            applicant=request.user,
            status__in=['draft', 'in_progress']
        ).first()
        
        if not application:
            return Response(
                {'message': 'No active application found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApplicationDetailSerializer(application, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get application progress",
        description="Get the progress of the current application (steps completed)",
        tags=['Applications']
    )
    @action(detail=False, methods=['get'], url_path='progress')
    def progress(self, request):
        """Get application progress for the current user"""
        application = Application.objects.filter(
            applicant=request.user,
            status__in=['draft', 'in_progress']
        ).first()
        
        if not application:
            return Response({
                'has_application': False,
                'current_step': 0,
                'steps': {
                    'parent_info': False,
                    'children_info': False,
                    'submitted': False
                }
            })
        
        has_parent = hasattr(application, 'applicant_parent') and application.applicant_parent
        has_children = application.applicant_children.count() > 0
        
        return Response({
            'has_application': True,
            'application_id': str(application.id),
            'status': application.status,
            'current_step': application.current_step,
            'steps': {
                'parent_info': has_parent,
                'children_info': has_children,
                'submitted': application.status not in ['draft', 'in_progress']
            }
        })


@extend_schema_view(
    list=extend_schema(
        summary="List all applications",
        description="Retrieve all applications for admin review with pagination",
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
        description="Get statistics about applications for dashboard",
        tags=['Admin - Applications']
    )
)
class AdminApplicationViewSet(viewsets.GenericViewSet):
    """
    Admin-only ViewSet for managing applications.
    
    URL Structure:
    - GET    /api/admin/applications/                          - List all applications
    - GET    /api/admin/applications/{id}/                     - Get application details
    - POST   /api/admin/applications/{id}/review/              - Approve or reject
    - POST   /api/admin/applications/{id}/mark-under-review/   - Mark as under review
    - POST   /api/admin/applications/bulk-update/              - Bulk update statuses
    - GET    /api/admin/applications/stats/                    - Get statistics
    """
    
    # permission_classes = [permissions.IsAuthenticated, IsAdmin]
    pagination_class = CustomPageNumberPagination
    queryset = Application.objects.all().select_related(
        'applicant', 'applicant_parent'
    ).prefetch_related('applicant_children')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = [
        'applicant__email', 'applicant__first_name', 'applicant__last_name',
        'applicant_parent__full_name', 'applicant_parent__email'
    ]
    ordering_fields = ['created_at', 'submitted_at', 'status', 'applicant__first_name']
    ordering = ['-submitted_at', '-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'review':
            return ApplicationReviewSerializer
        return ApplicationDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List all applications with counts for dashboard and pagination.
        
        Response structure matches student list:
        {
            "count": 15,
            "page": 1,
            "page_size": 10,
            "total_pages": 2,
            "next_page": 2,
            "previous_page": null,
            "first_page": 1,
            "last_page": 2,
            "start_index": 1,
            "end_index": 10,
            "has_next": true,
            "has_previous": false,
            "counts": { ... },
            "results": [ ... ]
        }
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Counts for dashboard stats cards
        counts = {
            'pending_review': Application.objects.filter(status='submitted').count(),
            'under_review': Application.objects.filter(status='under_review').count(),
            'approved': Application.objects.filter(status='approved').count(),
            'rejected': Application.objects.filter(status='rejected').count(),
            'draft': Application.objects.filter(status='draft').count(),
            'in_progress': Application.objects.filter(status='in_progress').count(),
            'total': Application.objects.count()
        }
        
        # Apply pagination
        page = self.paginate_queryset(queryset)

        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Get paginated response with student-like structure
            paginated_response = self.get_paginated_response(serializer.data)
            # Add counts to the response
            paginated_response.data['counts'] = counts
            return paginated_response
        
        # Fallback for no pagination (shouldn't happen with pagination_class set)
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
    
    @extend_schema(
        summary="Review application",
        description="Approve or reject an application. For rejection, a reason can be provided.",
        request=ApplicationReviewSerializer,
        tags=['Admin - Applications']
    )
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
        
        serializer = ApplicationReviewSerializer(
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
    
    @extend_schema(
        summary="Mark as under review",
        description="Mark an application as under review (moves from submitted to under_review)",
        tags=['Admin - Applications']
    )
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
            'status': application.status,
            'application_id': str(application.id)
        })
    
    @extend_schema(
        summary="Get application statistics",
        description="Get comprehensive statistics about applications for dashboard",
        tags=['Admin - Applications']
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get application statistics for dashboard"""
        from datetime import timedelta
        
        # Overall counts
        total = Application.objects.count()
        submitted = Application.objects.filter(status='submitted').count()
        under_review = Application.objects.filter(status='under_review').count()
        approved = Application.objects.filter(status='approved').count()
        rejected = Application.objects.filter(status='rejected').count()
        draft = Application.objects.filter(status='draft').count()
        in_progress = Application.objects.filter(status='in_progress').count()
        
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
            avg_review_days = round(total_days / reviewed_apps.count(), 1)
        
        # Completion rate
        completion_rate = round((approved + rejected) / total * 100, 1) if total > 0 else 0
        
        return Response({
            'total': total,
            'submitted': submitted,
            'under_review': under_review,
            'approved': approved,
            'rejected': rejected,
            'draft': draft,
            'in_progress': in_progress,
            'this_month': this_month,
            'last_7_days': last_7_days,
            'average_review_days': avg_review_days,
            'completion_rate': completion_rate,
            'pending_percentage': round(submitted / total * 100, 1) if total > 0 else 0,
            'approved_percentage': round(approved / total * 100, 1) if total > 0 else 0,
            'rejected_percentage': round(rejected / total * 100, 1) if total > 0 else 0
        })
    
    @extend_schema(
        summary="Bulk update applications",
        description="Update status for multiple applications at once",
        request={
            'type': 'object',
            'properties': {
                'application_ids': {'type': 'array', 'items': {'type': 'string'}},
                'status': {'type': 'string', 'enum': ['under_review', 'approved', 'rejected']}
            }
        },
        tags=['Admin - Applications']
    )
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
        
        # Update the applications
        applications.update(status=new_status)
        
        # If approving/rejecting, set reviewed_at
        if new_status in ['approved', 'rejected']:
            applications.update(reviewed_at=timezone.now())
        
        return Response({
            'message': f'Successfully updated {count} applications to {new_status}',
            'updated_count': count,
            'status': new_status
        })