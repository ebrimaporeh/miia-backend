# apps/accounts/views/batch_enrollment_views.py

import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.accounts.models import Student, Parent
from apps.accounts.serializers.student_serializers import (
    BatchEnrollmentSerializer,
    BatchEnrollmentResponseSerializer
)
from apps.accounts.utils.student_utils import (
    create_parent_user,
    create_student_user,
    update_parent_profile,
    update_student_profile,
    generate_student_id,
    
)
from apps.accounts.email_utils import (send_enrollment_confirmation_email,
    send_student_enrollment_email)
from apps.accounts.permissions import IsAdmin
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema_view(
    enroll=extend_schema(
        summary="Batch enroll students",
        description="""
        Enroll multiple students under a single parent/guardian.
        
        Features:
        - Create new parent or use existing parent
        - Enroll multiple students at once
        - Partial success handling (some students may fail, others succeed)
        - Detailed error reporting for each student
        - Optional email notifications
        """,
        request=BatchEnrollmentSerializer,
        responses={201: BatchEnrollmentResponseSerializer},
        tags=['Students - Batch Enrollment'],
    )
)
class BatchEnrollmentViewSet(viewsets.GenericViewSet):
    """ViewSet for batch enrollment operations"""
    
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def get_serializer_class(self):
        if self.action == 'enroll':
            return BatchEnrollmentSerializer
        return BatchEnrollmentSerializer
    
    @action(detail=False, methods=['post'], url_path='enroll')
    def enroll(self, request):
        """
        Enroll multiple students under a single parent/guardian.
        """
        serializer = BatchEnrollmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'error': 'Validation failed',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            result = self._process_batch_enrollment(validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Batch enrollment failed: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'error': f'Batch enrollment failed: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_batch_enrollment(self, data):
        """
        Process batch enrollment with partial failure handling.
        
        Strategy:
        1. Create/Get parent first (critical)
        2. If parent creation fails, entire batch fails
        3. For each student, attempt enrollment individually
        4. Track successes and failures
        5. Return detailed results
        """
        parent_id = data.get('parent_id')
        send_invitation = data.get('send_invitation', True)
        students_data = data.get('students', [])
        
        # Track results
        successful_enrollments = []
        failed_enrollments = []
        
        try:
            with transaction.atomic():
                # STEP 1: Create or get parent (critical - if fails, entire batch fails)
                parent_user, parent_profile, parent_password, is_new_parent = self._get_or_create_parent(data)
                
                logger.info(f"Parent processed: {parent_user.email} (new: {is_new_parent})")
            
            # STEP 2: Enroll each student (outside atomic to allow partial success)
            for index, student_data in enumerate(students_data):
                try:
                    with transaction.atomic():
                        enrollment_result = self._enroll_single_student(
                            student_data=student_data,
                            parent_user=parent_user,
                            parent_profile=parent_profile,
                            parent_password=parent_password if is_new_parent else None,
                            is_new_parent=is_new_parent,
                            send_invitation=send_invitation
                        )
                        successful_enrollments.append(enrollment_result)
                        logger.info(f"Successfully enrolled student: {enrollment_result['student']['email']}")
                        
                except Exception as e:
                    # Log the error but continue with other students
                    error_msg = str(e)
                    logger.error(f"Failed to enroll student #{index + 1}: {error_msg}")
                    failed_enrollments.append({
                        'student_data': student_data,
                        'error': error_msg,
                        'index': index
                    })
            
            # STEP 3: Prepare response
            total = len(students_data)
            successful = len(successful_enrollments)
            failed = len(failed_enrollments)
            
            response_data = {
                'status': 'partial_success' if failed > 0 else 'success',
                'total': total,
                'successful': successful,
                'failed': failed,
                'parent': {
                    'email': parent_user.email,
                    'first_name': parent_user.first_name,
                    'last_name': parent_user.last_name,
                    'email': parent_user.email,
                    'relationship': parent_profile.relationship,
                    'is_new': is_new_parent
                },
                'successful_enrollments': successful_enrollments,
                'failed_enrollments': failed_enrollments,
                'email_sent': send_invitation
            }
            
            # Only include parent password if new parent was created
            if is_new_parent and parent_password:
                response_data['parent_password'] = parent_password
            
            return response_data
            
        except Exception as e:
            # Parent creation failed - entire batch fails
            logger.error(f"Parent creation failed: {str(e)}")
            return {
                'status': 'error',
                'total': len(students_data),
                'successful': 0,
                'failed': len(students_data),
                'error': f'Parent creation failed: {str(e)}',
                'successful_enrollments': [],
                'failed_enrollments': [
                    {'student_data': s, 'error': str(e), 'index': i}
                    for i, s in enumerate(students_data)
                ]
            }
            
    def _get_or_create_parent(self, data):
        """
        Get existing parent or create new one.
        Uses email for identification.
        Returns: (parent_user, parent_profile, parent_password, is_new_parent)
        """
        parent_email = data.get('parent_email')
        
        if parent_email:
            # Use existing parent by email
            try:
                parent_user = User.objects.get(email=parent_email, role='parent')
                parent_profile = parent_user.parent_profile
                parent_password = None
                is_new_parent = False
                
                # Update parent profile with new information if provided
                update_data = {}
                if data.get('guardian_phone'):
                    update_data['phone'] = data.get('guardian_phone')
                if data.get('address'):
                    update_data['address'] = data.get('address')
                if data.get('guardian_relationship'):
                    update_data['relationship'] = data.get('guardian_relationship')
                
                if update_data:
                    update_parent_profile(parent_profile, **update_data)
                
                return parent_user, parent_profile, parent_password, is_new_parent
                
            except User.DoesNotExist:
                raise Exception(f"Parent with email {parent_email} does not exist")
            except Parent.DoesNotExist:
                raise Exception(f"Parent profile for {parent_email} does not exist")
        
        # Create new parent - EMAIL IS REQUIRED
        guardian_email = data.get('guardian_email')
        
        if not guardian_email:
            raise Exception("Parent email is required. Please provide guardian_email.")
        
        guardian_name = data.get('guardian_name', '')
        name_parts = guardian_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        guardian_phone = data.get('guardian_phone', '')
        guardian_relationship = data.get('guardian_relationship', 'parent')
        address = data.get('address', '')
        
        # Check if parent already exists by email
        existing_parent_user = User.objects.filter(email=guardian_email, role='parent').first()
        
        if existing_parent_user:
            parent_user = existing_parent_user
            parent_profile = parent_user.parent_profile
            parent_password = None
            is_new_parent = False
            
            # Update existing profile
            update_parent_profile(
                parent_profile,
                relationship=guardian_relationship,
                phone=guardian_phone,
                address=address
            )
        else:
            # Create new parent user - email is required
            parent_user, parent_password = create_parent_user(
                first_name=first_name,
                last_name=last_name,
                email=guardian_email,  # Email is now required
                is_active=True
            )
            parent_profile = parent_user.parent_profile
            is_new_parent = True
            
            # Update profile with additional info
            update_parent_profile(
                parent_profile,
                relationship=guardian_relationship,
                phone=guardian_phone,
                address=address
            )
        
        return parent_user, parent_profile, parent_password, is_new_parent


    def _enroll_single_student(self, student_data, parent_user, parent_profile, 
                                parent_password, is_new_parent, send_invitation):
        """
        Enroll a single student.
        Returns: enrollment result dict
        """
        # Create student user
        student_user, student_password = create_student_user(
            first_name=student_data.get('first_name', ''),
            last_name=student_data.get('last_name', ''),
            email=None,  # Auto-generate email
            is_active=True
        )
        
        # Get or create student profile
        student_profile = student_user.student_profile
        
        # Prepare enrollment date
        enrollment_date = timezone.now().date()
        
        # Determine guardian relationship (student override or parent's relationship)
        guardian_relationship = student_data.get('guardian_relationship') or parent_profile.relationship
        
        # Update student profile
        student_profile = update_student_profile(
            student_profile,
            student_id=generate_student_id(),
            enrollment_date=enrollment_date,
            date_of_birth=student_data.get('date_of_birth'),
            gender=student_data.get('gender', ''),
            phone=student_data.get('phone', ''),
            department=student_data.get('department', ''),
            status='active',
            performance='average',
            has_allergies=student_data.get('has_allergies', False),
            allergy_details=student_data.get('allergy_details', ''),
            medical_conditions=student_data.get('medical_conditions', ''),
            guardian_name=f"{parent_user.first_name} {parent_user.last_name}",
            guardian_phone=parent_profile.phone,
            guardian_email=parent_user.email,
            guardian_relationship=guardian_relationship,
        )
        
        # Link student to parent
        student_profile.parent = parent_profile
        student_profile.save()
        
        # Send emails if requested
        email_sent = False
        if send_invitation:
            try:
                # Send email to parent (only for new parent or first student?)
                # For existing parent, only send for the first student to avoid spam
                if is_new_parent:
                    send_enrollment_confirmation_email(
                        parent_user=parent_user,
                        student_user=student_user,
                        student_profile=student_profile,
                        student_password=student_password,
                        parent_password=parent_password,
                    )
                
                # Send email to student
                if student_user.email:
                    send_student_enrollment_email(
                        student_user=student_user,
                        student_password=student_password,
                        student_profile=student_profile,
                    )
                email_sent = True
            except Exception as e:
                logger.warning(f"Failed to send emails for student {student_user.email}: {e}")
        
        return {
            'student': {
                'id': str(student_profile.user.id),
                'first_name': student_user.first_name,
                'last_name': student_user.last_name,
                'email': student_user.email,
                'student_id': student_profile.student_id,
                'status': student_profile.status,
            },
            'guardian_relationship': guardian_relationship,
            'credentials': {
                'student_password': student_password,
            },
            'email_sent': email_sent
        }