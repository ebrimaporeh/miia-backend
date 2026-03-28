# apps/applications/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.applications.models import Application
from apps.applications.serializers import (
    ApplicationSerializer,
    ApplicationListSerializer,
    CreateApplicationSerializer,
    UpdateApplicationSerializer,
    SubmitApplicationSerializer,
    ReviewApplicationSerializer
)
from apps.accounts.permissions import IsAdmin, IsParent


@extend_schema_view(
    list=extend_schema(summary="List applications", tags=['Applications']),
    retrieve=extend_schema(summary="Get application details", tags=['Applications']),
    create=extend_schema(summary="Create application (Step 1)", tags=['Applications']),
    update=extend_schema(summary="Update application (Steps 2-5)", tags=['Applications']),
    partial_update=extend_schema(summary="Partially update application", tags=['Applications']),
    destroy=extend_schema(summary="Delete application", tags=['Applications'])
)
class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing applications"""
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'current_step']
    search_fields = ['applicant__email', 'applicant__first_name', 'applicant__last_name']
    ordering_fields = ['created_at', 'submitted_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateApplicationSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateApplicationSerializer
        elif self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'submit':
            return SubmitApplicationSerializer
        elif self.action == 'review':
            return ReviewApplicationSerializer
        return ApplicationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            # permission_classes = [permissions.IsAuthenticated]
            permission_classes = [permissions.AllowAny]

            # permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'submit']:
            permission_classes = [permissions.IsAuthenticated, IsParent]
        elif self.action in ['destroy', 'review']:
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Application.objects.none()
        
        if user.role == 'admin':
            return Application.objects.all().select_related('applicant', 'parent').prefetch_related('children')
        
        if user.role == 'parent':
            return Application.objects.filter(applicant=user).select_related('applicant', 'parent').prefetch_related('children')
        
        return Application.objects.none()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit application for review (Step 6)"""
        application = self.get_object()
        
        if application.applicant != request.user:
            return Response(
                {'error': 'You do not have permission to submit this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.status in ['submitted', 'under_review', 'approved', 'completed']:
            return Response(
                {'error': f'Application already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SubmitApplicationSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            application = serializer.save()
            return Response(ApplicationSerializer(application).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my')
    def my_applications(self, request):
        """Get current user's applications"""
        applications = Application.objects.filter(applicant=request.user).order_by('-created_at')
        serializer = ApplicationListSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='current')
    def current_application(self, request):
        """Get current user's active application"""
        application = Application.objects.filter(
            applicant=request.user,
            # status__in=['draft', 'in_progress']
        ).order_by('-created_at').first()
        
        if not application:
            return Response(
                {'message': 'No active application found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)


class AdminApplicationViewSet(viewsets.GenericViewSet):
    """Admin-only ViewSet for managing applications"""
    
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Application.objects.all().select_related('applicant', 'parent').prefetch_related('children')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['applicant__email', 'applicant__first_name', 'applicant__last_name']
    ordering_fields = ['created_at', 'submitted_at']
    ordering = ['-submitted_at']
    
    def list(self, request):
        """List all applications with counts"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Counts for dashboard
        counts = {
            'pending_review': Application.objects.filter(status='submitted').count(),
            'under_review': Application.objects.filter(status='under_review').count(),
            'approved': Application.objects.filter(status='approved').count(),
            'rejected': Application.objects.filter(status='rejected').count(),
            'total': Application.objects.count()
        }
        
        page = self.paginate_queryset(queryset)
        if page:
            serializer = ApplicationListSerializer(page, many=True)
            return Response({
                'counts': counts,
                'results': serializer.data
            })
        
        serializer = ApplicationListSerializer(queryset, many=True)
        return Response({
            'counts': counts,
            'results': serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get application details"""
        application = self.get_object()
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Approve or reject application"""
        application = self.get_object()
        
        if application.status in ['approved', 'rejected', 'completed']:
            return Response(
                {'error': f'Application already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewApplicationSerializer(
            application,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            return Response(ApplicationSerializer(application).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get application statistics"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total = Application.objects.count()
        submitted = Application.objects.filter(status='submitted').count()
        under_review = Application.objects.filter(status='under_review').count()
        approved = Application.objects.filter(status='approved').count()
        rejected = Application.objects.filter(status='rejected').count()
        
        # Average review time
        reviewed_apps = Application.objects.exclude(reviewed_at=None).exclude(submitted_at=None)
        avg_review_days = 0
        if reviewed_apps.exists():
            total_days = sum((app.reviewed_at - app.submitted_at).days for app in reviewed_apps)
            avg_review_days = total_days / reviewed_apps.count()
        
        return Response({
            'total': total,
            'submitted': submitted,
            'under_review': under_review,
            'approved': approved,
            'rejected': rejected,
            'this_month': Application.objects.filter(created_at__gte=start_of_month).count(),
            'last_7_days': Application.objects.filter(created_at__gte=now - timedelta(days=7)).count(),
            'average_review_days': round(avg_review_days, 1),
            'completion_rate': round((approved + rejected) / total * 100, 1) if total > 0 else 0
        })