from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from ..serializers.auth_serializers import UserProfileSerializer, RegisterSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations"""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        return UserProfileSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get users by type"""
        role = request.query_params.get('type', None)
        if role:
            users = self.queryset.filter(role=role)
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response({'error': 'Type parameter required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create users"""
        users_data = request.data.get('users', [])
        created_users = []
        errors = []
        
        for user_data in users_data:
            serializer = RegisterSerializer(data=user_data)
            if serializer.is_valid():
                user = serializer.save()
                created_users.append(UserProfileSerializer(user).data)
            else:
                errors.append({'data': user_data, 'errors': serializer.errors})
        
        return Response({
            'created': created_users,
            'errors': errors,
            'total_created': len(created_users),
            'total_errors': len(errors)
        })