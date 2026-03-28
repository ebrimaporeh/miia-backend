from rest_framework import viewsets, permissions
from ..models import Teacher
from ..serializers.auth_serializers import TeacherProfileSerializer

class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing teachers"""
    queryset = Teacher.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filters if needed
        class_id = self.request.query_params.get('class', None)
        if class_id:
            queryset = queryset.filter(
                teaching_assignments__class_group_id=class_id
            ).distinct()
        return queryset