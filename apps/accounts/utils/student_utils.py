# apps/accounts/utils/student_utils.py
import random
import string
from django.contrib.auth import get_user_model
from apps.accounts.models import Student

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


def create_student_user(first_name, last_name, email=None, password=None, is_active=True):
    """
    Create a student user account without creating a student profile
    """
    from apps.accounts.models import Student
    
    # Generate email if not provided
    if not email:
        email = generate_student_email(first_name, last_name)
    
    # Generate username
    username = generate_student_username(first_name, last_name)
    
    # Use default password if not provided
    if not password:
        password = Student.STUDENT_DEFAULT_PASSWORD
    
    # Create user
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
    
    return user


def create_student_profile(user, **kwargs):
    """
    Create a student profile for an existing user
    """
    from apps.accounts.models import Student
    
    # Generate student ID if not provided
    student_id = kwargs.pop('student_id', None)
    if not student_id:
        student_id = generate_student_id()
    
    # Create student profile (this won't trigger duplicate since we're creating directly)
    student = Student.objects.create(
        user=user,
        student_id=student_id,
        enrollment_date=kwargs.pop('enrollment_date', None),
        **kwargs
    )
    
    return student


def create_student(first_name, last_name, email=None, password=None, is_active=True, **student_data):
    """
    Complete student creation (user + profile) with proper defaults
    """
    # Create user account (this will NOT create a student profile due to signal change)
    user = create_student_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_active=is_active
    )
    
    # Now create the student profile
    student = create_student_profile(user, **student_data)
    
    return student


def update_student_email(student, new_email):
    """
    Update student's email with validation
    """
    if User.objects.filter(email=new_email).exclude(id=student.user.id).exists():
        raise ValueError("Email already exists")
    
    student.user.email = new_email
    student.user.save()
    return student


def reset_student_password(student):
    """
    Reset student password to default
    """
    from apps.accounts.models import Student
    student.user.set_password(Student.STUDENT_DEFAULT_PASSWORD)
    student.user.save()
    return Student.STUDENT_DEFAULT_PASSWORD