# apps/accounts/views/parent_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.accounts.models import Parent, Student
from apps.accounts.serializers.parent_serializers import (
    ParentProfileSerializer,
    ParentChildSerializer,
    ParentUpdateProfileSerializer,
    ParentChildCreateSerializer,
    ParentChildUpdateSerializer,
)
from apps.accounts.permissions import IsParent
from apps.applications.models import Application


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get parent profile",
        description="Retrieve parent profile with children and application status",
        tags=['Parent']
    ),
    update=extend_schema(
        summary="Update parent profile",
        description="Update parent profile information",
        tags=['Parent']
    ),
    partial_update=extend_schema(
        summary="Partially update parent profile",
        description="Partially update parent profile information",
        tags=['Parent']
    ),
)
class ParentProfileViewSet(viewsets.GenericViewSet):
    """ViewSet for parent profile management"""
    
    permission_classes = [permissions.IsAuthenticated, IsParent]
    serializer_class = ParentProfileSerializer
    
    def get_object(self):
        """Get the parent profile for the current user"""
        return get_object_or_404(Parent, user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Get parent profile"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update parent profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = ParentUpdateProfileSerializer(
            instance, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(ParentProfileSerializer(instance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update parent profile"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def children(self, request):
        """Get all children of the parent"""
        parent = self.get_object()
        children = parent.children.all().order_by('user__first_name')
        serializer = ParentChildSerializer(children, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def application(self, request):
        """Get parent's current application"""
        try:
            application = Application.objects.get(applicant=request.user)
            from apps.applications.serializers import ApplicationSerializer
            serializer = ApplicationSerializer(application, context={'request': request})
            return Response(serializer.data)
        except Application.DoesNotExist:
            return Response(
                {'message': 'No application found'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    list=extend_schema(
        summary="List children",
        description="List all children of the current parent",
        tags=['Parent Children']
    ),
    create=extend_schema(
        summary="Add child",
        description="Add a new child during registration",
        tags=['Parent Children']
    ),
    retrieve=extend_schema(
        summary="Get child details",
        description="Get details of a specific child",
        tags=['Parent Children']
    ),
    update=extend_schema(
        summary="Update child",
        description="Update child information (limited fields)",
        tags=['Parent Children']
    ),
    partial_update=extend_schema(
        summary="Partially update child",
        description="Partially update child information",
        tags=['Parent Children']
    ),
    destroy=extend_schema(
        summary="Delete child",
        description="Delete a child (only if pending approval)",
        tags=['Parent Children']
    ),
)
class ParentChildrenViewSet(viewsets.ModelViewSet):
    """ViewSet for parents to manage their children"""
    
    permission_classes = [permissions.IsAuthenticated, IsParent]
    serializer_class = ParentChildSerializer
    
    def get_queryset(self):
        """Get children belonging to the parent"""
        # Get the parent profile for the current user
        parent = get_object_or_404(Parent, user=self.request.user)
        
        # Return all students where this parent is linked via the parent field
        queryset = Student.objects.filter(parent=parent)
        
        # Also include students where parent is linked via guardian_email (for backward compatibility)
        if not queryset.exists():
            queryset = Student.objects.filter(guardian_email=self.request.user.email)
        
        # Select related to optimize queries (no prefetch_related needed for ForeignKey)
        return queryset.select_related('user', 'parent__user')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ParentChildCreateSerializer
        return ParentChildSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """List all children of the parent"""
        queryset = self.get_queryset()
        
        # Debug: Print to console
        print(f"Parent: {request.user.email}")
        print(f"Children count: {queryset.count()}")
        for child in queryset:
            print(f"Child: {child.name}, ID: {child.student_id}, Parent ID: {child.parent_id}")
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Add a new child"""
        parent = get_object_or_404(Parent, user=request.user)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response(
                ParentChildSerializer(student, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get a specific child"""
        instance = self.get_object()
        
        # Verify that this child belongs to the parent
        parent = get_object_or_404(Parent, user=request.user)
        if instance.parent_id != parent.id:
            return Response(
                {'error': 'This child does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update a child (limited fields)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verify that this child belongs to the parent
        parent = get_object_or_404(Parent, user=request.user)
        if instance.parent_id != parent.id:
            return Response(
                {'error': 'This child does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow updating specific fields
        allowed_fields = [
            'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'phone', 'address', 'has_allergies', 'allergy_details', 'medical_conditions', 'notes'
        ]
        
        # Filter data to only allowed fields
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=filtered_data, partial=partial)
        if serializer.is_valid():
            student = serializer.save()
            return Response(ParentChildSerializer(student, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a child (only if pending approval)"""
        instance = self.get_object()
        
        # Verify that this child belongs to the parent
        parent = get_object_or_404(Parent, user=request.user)
        if instance.parent_id != parent.id:
            return Response(
                {'error': 'This child does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow deletion if student is pending
        if instance.status != 'pending':
            return Response(
                {'error': 'Cannot delete approved or active students. Please contact administration.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete the student and user
        user = instance.user
        instance.delete()
        user.delete()
        
        return Response(
            {'message': 'Child removed successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
