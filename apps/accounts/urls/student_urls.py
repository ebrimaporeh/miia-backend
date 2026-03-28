# apps/accounts/urls/student_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views.student_views import StudentViewSet, StudentDocumentViewSet, StudentNoteViewSet

router = DefaultRouter()
router.register(r'', StudentViewSet, basename='student')

# Nested routes for documents and notes
student_document_list = StudentDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
student_document_detail = StudentDocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})
student_note_list = StudentNoteViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
student_note_detail = StudentNoteViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    # Include router URLs for the main student endpoints
    path('', include(router.urls)),
    
    # Nested routes for documents
    path('<uuid:pk>/documents/', student_document_list, name='student-documents'),
    path('<uuid:pk>/documents/<uuid:document_pk>/', student_document_detail, name='student-document-detail'),
    
    # Nested routes for notes
    path('<uuid:pk>/notes/', student_note_list, name='student-notes'),
    path('<uuid:pk>/notes/<uuid:note_pk>/', student_note_detail, name='student-note-detail'),
]