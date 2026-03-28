from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.accounts.models import Staff
from apps.accounts.serializers.auth_serializers import StaffProfileSerializer, UserProfileSerializer


class StaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing staff profiles.
    
    Provides:
    - List all staff members
    - Retrieve specific staff member details
    - Create new staff member (admin only)
    - Update staff member (admin only)
    - Delete staff member (admin only)
    - Custom actions for department filtering
    """
    queryset = Staff.objects.all().select_related('user').order_by('-joining_date')
    serializer_class = StaffProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Assign permissions based on action:
        - List and retrieve: Authenticated users
        - Create, update, delete: Admin only
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_create']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Optionally filter staff by department
        """
        queryset = super().get_queryset()
        
        # Filter by department if provided
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        # Filter by search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__email__icontains=search) |
                models.Q(staff_id__icontains=search) |
                models.Q(department__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def departments(self, request):
        """
        Get list of unique departments
        """
        departments = Staff.objects.values_list('department', flat=True).distinct()
        return Response({
            'departments': [dept for dept in departments if dept]
        })
    
    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """
        Get staff grouped by department
        """
        department = request.query_params.get('department', None)
        if not department:
            return Response(
                {'error': 'Department parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        staff_members = self.get_queryset().filter(department=department)
        serializer = self.get_serializer(staff_members, many=True)
        return Response({
            'department': department,
            'count': staff_members.count(),
            'staff': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create staff members (admin only)
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff_data = request.data.get('staff', [])
        created_staff = []
        errors = []
        
        for index, data in enumerate(staff_data):
            # First create or get user
            user_data = {
                'email': data.get('email'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'role': 'staff',
                'phone': data.get('phone', ''),
            }
            
            from apps.accounts.serializers import RegisterSerializer
            user_serializer = RegisterSerializer(data=user_data)
            
            if user_serializer.is_valid():
                user = user_serializer.save()
                
                # Then create staff profile
                staff_data = {
                    'user': user,
                    'staff_id': data.get('staff_id', f"STF{user.id.hex[:8].upper()}"),
                    'department': data.get('department', ''),
                    'position': data.get('position', ''),
                    'joining_date': data.get('joining_date', user.date_joined.date()),
                }
                
                try:
                    staff = Staff.objects.create(**staff_data)
                    created_staff.append(StaffProfileSerializer(staff).data)
                except Exception as e:
                    errors.append({
                        'index': index,
                        'data': data,
                        'error': str(e)
                    })
            else:
                errors.append({
                    'index': index,
                    'data': data,
                    'errors': user_serializer.errors
                })
        
        return Response({
            'created': created_staff,
            'errors': errors,
            'total_created': len(created_staff),
            'total_errors': len(errors)
        })
    
    @action(detail=True, methods=['patch'])
    def update_department(self, request, pk=None):
        """
        Update staff member's department
        """
        staff = self.get_object()
        department = request.data.get('department')
        
        if not department:
            return Response(
                {'error': 'Department field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        staff.department = department
        staff.save()
        
        serializer = self.get_serializer(staff)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_position(self, request, pk=None):
        """
        Update staff member's position
        """
        staff = self.get_object()
        position = request.data.get('position')
        
        if not position:
            return Response(
                {'error': 'Position field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        staff.position = position
        staff.save()
        
        serializer = self.get_serializer(staff)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about staff
        """
        total_staff = self.queryset.count()
        
        # Department breakdown
        departments = {}
        for dept in Staff.objects.values_list('department', flat=True).distinct():
            if dept:
                departments[dept] = Staff.objects.filter(department=dept).count()
        
        # Recent joins (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_joins = Staff.objects.filter(joining_date__gte=thirty_days_ago).count()
        
        return Response({
            'total_staff': total_staff,
            'departments': departments,
            'recent_joins': recent_joins,
            'department_count': len(departments)
        })