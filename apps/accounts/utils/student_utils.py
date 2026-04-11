# apps/accounts/utils/student_utils.py
import random
import string
import logging
from django.contrib.auth import get_user_model



logger = logging.getLogger(__name__)
User = get_user_model()


def generate_student_email(first_name, last_name):
    """
    Generate a unique email for a student
    Format: firstname.lastname@miia.edu
    If taken, add a number suffix
    """
    base_email = f"{first_name.lower()}.{last_name.lower()}@miia.edu"
    email = base_email
    counter = 1
    
    while User.objects.filter(email=email).exists():
        email = f"{first_name.lower()}.{last_name.lower()}{counter}@miia.edu"
        counter += 1
    
    return email


def generate_parent_email(first_name, last_name):
    """
    Generate a unique email for a parent if not provided
    """
    base_email = f"{first_name.lower()}.{last_name.lower()}.parent@miia.edu"
    email = base_email
    counter = 1
    
    while User.objects.filter(email=email).exists():
        email = f"{first_name.lower()}.{last_name.lower()}.parent{counter}@miia.edu"
        counter += 1
    
    return email


def generate_parent_username(first_name, last_name):
    """
    Generate a unique username for a parent
    """
    base_username = f"{first_name.lower()}.{last_name.lower()}.parent"
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


def generate_student_username(first_name, last_name):
    """
    Generate a unique username for a student
    """
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


def generate_student_id():
    """
    Generate a unique student ID
    Format: STU followed by random 8 characters
    """
    import uuid
    return f"STU{str(uuid.uuid4()).replace('-', '')[:8].upper()}"


def generate_secure_password(length=12):
    """
    Generate a secure random password
    """
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))


def create_student_user(first_name, last_name, email=None, password=None, is_active=True):
    """
    Create a student user account.
    NOTE: The signal will automatically create a Student profile.
    So we don't create the profile here.
    """
    # Generate email if not provided
    if not email:
        email = generate_student_email(first_name, last_name)
    
    # Generate username
    username = generate_student_username(first_name, last_name)
    
    # Generate password if not provided
    if not password:
        password = generate_secure_password()
    
    # Create user - signal will create Student profile automatically
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role='student',
        is_active=is_active
    )
    
    # Set password
    user.set_password(password)
    user.save()
    
    return user, password


def create_parent_user(first_name, last_name, email, password=None, is_active=True):
    """
    Create a parent user account.
    NOTE: Email is REQUIRED - will not auto-generate.
    """
    if not email:
        raise ValueError("Parent email is required")
    
    # Generate username from email
    username = generate_parent_username(first_name, last_name)
    
    # Generate password if not provided
    if not password:
        password = generate_secure_password()
    
    # Create user - signal will create Parent profile automatically
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role='parent',
        is_active=is_active
    )
    
    # Set password
    user.set_password(password)
    user.save()
    
    return user, password


def update_student_profile(student, **kwargs):
    """
    Update an existing student profile with additional data
    """
    # Fields that can be updated
    updatable_fields = [
        'date_of_birth', 'gender', 'phone', 'address', 'department',
        'status', 'performance', 'graduation_date', 'has_allergies',
        'allergy_details', 'medical_conditions', 'notes',
        'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
    ]
    
    updated = False
    for field in updatable_fields:
        if field in kwargs and kwargs[field] is not None:
            value = kwargs[field]
            # Handle empty strings for optional fields
            if value == '' and field not in ['date_of_birth', 'graduation_date']:
                setattr(student, field, value)
                updated = True
            elif value:
                setattr(student, field, value)
                updated = True
    
    # Handle enrollment_date separately
    if 'enrollment_date' in kwargs and kwargs['enrollment_date']:
        student.enrollment_date = kwargs['enrollment_date']
        updated = True
    
    if updated:
        student.save()
    
    return student


def update_parent_profile(parent, **kwargs):
    """
    Update an existing parent profile with additional data
    """
    # Fields that can be updated
    updatable_fields = ['relationship', 'phone', 'alternate_phone', 'address', 'occupation']
    
    updated = False
    for field in updatable_fields:
        if field in kwargs and kwargs[field] is not None:
            value = kwargs[field]
            if value or value == '':
                setattr(parent, field, value)
                updated = True
    
    if updated:
        parent.save()
    
    return parent

# def enroll_student(form_data):
#     """
#     Enroll a new student with parent/guardian information.
    
#     This function handles the complete enrollment process:
#     1. Creates parent/guardian user (signal auto-creates Parent profile)
#     2. Creates student user (signal auto-creates Student profile)
#     3. Updates both profiles with additional data
#     4. Links student to parent
#     5. Sends email invitations (optional)
#     """
    
#     try:
#         with transaction.atomic():
#             # Parse guardian name
#             guardian_full_name = form_data.get('guardian_name', '')
#             guardian_first_name = guardian_full_name.split(' ')[0] if guardian_full_name else ''
#             guardian_last_name = ' '.join(guardian_full_name.split(' ')[1:]) if guardian_full_name else ''
            
#             logger.info(f"Enrolling student: {form_data.get('first_name')} {form_data.get('last_name')}")
            
#             # Check if parent already exists by email
#             parent_email = form_data.get('guardian_email')
#             existing_parent_user = User.objects.filter(email=parent_email, role='parent').first()
#             is_new_parent = not existing_parent_user
            
#             if existing_parent_user:
#                 # Parent already exists - use existing parent
#                 logger.info(f"Parent already exists: {parent_email}")
#                 parent_user = existing_parent_user
#                 parent_profile = parent_user.parent_profile
#                 parent_password = None  # No password generated for existing parent
                
#                 # Update existing parent profile with new info
#                 parent_profile = update_parent_profile(
#                     parent_profile,
#                     relationship=form_data.get('guardian_relationship', 'parent'),
#                     phone=form_data.get('guardian_phone', ''),
#                     address=form_data.get('address', ''),
#                     occupation=form_data.get('guardian_occupation', ''),
#                 )
#             else:
#                 # Create new parent user (signal auto-creates Parent profile)
#                 parent_user, parent_password = create_parent_user(
#                     first_name=guardian_first_name,
#                     last_name=guardian_last_name,
#                     email=parent_email,
#                     is_active=True
#                 )
#                 logger.info(f"Created new parent user: {parent_user.email}")
                
#                 # Get the auto-created parent profile and update it
#                 parent_profile = parent_user.parent_profile
#                 parent_profile = update_parent_profile(
#                     parent_profile,
#                     relationship=form_data.get('guardian_relationship', 'parent'),
#                     phone=form_data.get('guardian_phone', ''),
#                     address=form_data.get('address', ''),
#                     occupation=form_data.get('guardian_occupation', ''),
#                 )
            
#             # Create student user (signal auto-creates Student profile)
#             student_user, student_password = create_student_user(
#                 first_name=form_data.get('first_name', ''),
#                 last_name=form_data.get('last_name', ''),
#                 email=form_data.get('email'),
#                 is_active=True
#             )
#             logger.info(f"Created student user: {student_user.email}")
            
#             # Get the auto-created student profile and update it
#             student_profile = student_user.student_profile
            
#             # Prepare enrollment date
#             enrollment_date = form_data.get('enrollment_date')
#             if not enrollment_date:
#                 enrollment_date = timezone.now().date()
            
#             # Update student profile with all data
#             student_profile = update_student_profile(
#                 student_profile,
#                 student_id=generate_student_id(),
#                 enrollment_date=enrollment_date,
#                 date_of_birth=form_data.get('date_of_birth'),
#                 gender=form_data.get('gender', ''),
#                 phone=form_data.get('phone', ''),
#                 address=form_data.get('address', ''),
#                 department=form_data.get('department', ''),
#                 status=form_data.get('status', 'active'),
#                 performance=form_data.get('performance', 'average'),
#                 graduation_date=form_data.get('graduation_date'),
#                 has_allergies=form_data.get('has_allergies', False),
#                 allergy_details=form_data.get('allergy_details', ''),
#                 medical_conditions=form_data.get('medical_conditions', ''),
#                 notes=form_data.get('notes', ''),
#                 guardian_name=guardian_full_name,
#                 guardian_phone=form_data.get('guardian_phone', ''),
#                 guardian_email=parent_user.email,
#                 guardian_relationship=form_data.get('guardian_relationship', 'parent'),
#                 emergency_contact_name=form_data.get('emergency_contact_name', ''),
#                 emergency_contact_phone=form_data.get('emergency_contact_phone', ''),
#                 emergency_contact_relationship=form_data.get('emergency_contact_relationship', ''),
#             )
            
#             # Link student to parent
#             student_profile.parent = parent_profile
#             student_profile.save()
            
#             logger.info(f"Successfully enrolled student: {student_user.email} with parent: {parent_user.email}")
            
#             # Prepare response data
#             response_data = {
#                 'status': 'success',
#                 'student': {
#                     'id': str(student_profile.user.id),
#                     'first_name': student_user.first_name,
#                     'last_name': student_user.last_name,
#                     'email': student_user.email,
#                     'student_id': student_profile.student_id,
#                     'status': student_profile.status,
#                 },
#                 'parent': {
#                     'id': str(parent_profile.user.id),
#                     'first_name': parent_user.first_name,
#                     'last_name': parent_user.last_name,
#                     'email': parent_user.email,
#                     'relationship': parent_profile.relationship,
#                 },
#                 'credentials': {
#                     'student_password': student_password,
#                 }
#             }
            
#             # Only include parent password if this is a new parent
#             if parent_password:
#                 response_data['credentials']['parent_password'] = parent_password
            
#             # Send email invitations if requested
#             if form_data.get('send_invitation', False):
#                 # Send email to parent
#                 send_enrollment_confirmation_email(
#                     parent_user=parent_user,
#                     student_user=student_user,
#                     student_profile=student_profile,
#                     student_password=student_password,
#                     parent_password=parent_password,
#                 )
                
#                 # Send email to student if they have an email address
#                 if student_user.email:
#                     send_student_enrollment_email(
#                         student_user=student_user,
#                         student_password=student_password,
#                         student_profile=student_profile,
#                     )
                
#                 response_data['email_sent'] = True
#             else:
#                 response_data['email_sent'] = False
            
#             return response_data
            
#     except Exception as e:
#         logger.error(f"Failed to enroll student: {e}", exc_info=True)
#         raise



def create_student(first_name, last_name, email=None, password=None, is_active=True, **student_data):
    """
    Complete student creation (user + profile) with proper defaults.
    This is a convenience function for creating a student without a parent.
    """
    # Create user account (signal will create Student profile)
    user, generated_password = create_student_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_active=is_active
    )
    
    # Get the auto-created profile and update it
    student = user.student_profile
    student = update_student_profile(student, **student_data)
    
    return student, generated_password if not password else password


def update_student_email(student, new_email):
    """
    Update student's email with validation
    """
    if User.objects.filter(email=new_email).exclude(id=student.user.id).exists():
        raise ValueError("Email already exists")
    
    student.user.email = new_email
    student.user.save()
    return student


