# seeders/auth_seeder.py
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.models import User, Teacher, Student, Parent, Staff
from apps.applications.models import Application
from .base_seeder import BaseSeeder

class AuthSeeder(BaseSeeder):
    """Seeder for authentication and user data - Islamic School Focus"""
    
    def seed(self):
        print("  📝 Creating groups and permissions...")
        self._create_groups()
        
        print("  👥 Creating users...")
        self._create_admin_users()
        self._create_teacher_users()
        self._create_student_users()
        self._create_parent_users()
        self._create_staff_users()
        
        print("  📊 Creating profiles...")
        self._create_teacher_profiles()
        self._create_student_profiles()
        self._create_parent_profiles()
        self._create_staff_profiles()
        
        print("  📋 Creating applications...")
        self._create_applications()
    
    def _create_groups(self):
        """Create user groups with appropriate permissions"""
        groups_data = {
            'admin': {'permissions': 'all'},
            'teacher': {
                'permissions': [
                    'course:view', 'course:edit', 'course:enroll',
                    'assignment:view', 'assignment:create', 'assignment:edit', 'assignment:grade',
                    'grade:view', 'grade:edit',
                    'schedule:view', 'schedule:attend',
                    'student:view', 'student:attendance:mark', 'student:progress:view',
                    'parent:view', 'parent:communicate',
                    'dashboard:view',
                ]
            },
            'student': {
                'permissions': [
                    'course:view',
                    'assignment:view', 'assignment:submit',
                    'grade:view',
                    'schedule:view', 'schedule:attend',
                    'student:view',
                    'dashboard:view',
                ]
            },
            'parent': {
                'permissions': [
                    'course:view',
                    'grade:view',
                    'schedule:view',
                    'student:view', 'student:progress:view', 'student:attendance:view',
                    'parent:view',
                    'dashboard:view',
                ]
            },
            'staff': {
                'permissions': [
                    'user:view',
                    'student:view', 'student:create', 'student:edit',
                    'parent:view', 'parent:communicate',
                    'teacher:view',
                    'schedule:view',
                    'fees:view', 'fees:create', 'fees:edit',
                    'dashboard:view',
                ]
            },
        }
        
        for group_name, group_data in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if group_data['permissions'] == 'all':
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
            else:
                for perm_codename in group_data['permissions']:
                    try:
                        perm = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        pass
            
            self.created_objects[f'group_{group_name}'] = group
    
    def _create_admin_users(self):
        """Create admin users"""
        admins = [
            {
                'email': 'admin@miia.edu',
                'username': 'admin_miia',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'password': 'Admin@123456'
            },
        ]
        
        for admin_data in admins:
            password = admin_data.pop('password')
            user, created = User.objects.get_or_create(
                email=admin_data['email'],
                defaults=admin_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.created_objects[f'admin_{user.email}'] = user
    
    def _create_teacher_users(self):
        """Create Islamic school teachers"""
        teachers_data = [
            # Quran & Islamic Studies Teachers
            {'first_name': 'Abdullah', 'last_name': 'Al-Rahman', 'specialization': 'Quran & Tajweed'},
            {'first_name': 'Fatima', 'last_name': 'Al-Zahra', 'specialization': 'Islamic Studies'},
            {'first_name': 'Omar', 'last_name': 'Ibn Khattab', 'specialization': 'Arabic Language'},
            {'first_name': 'Aisha', 'last_name': 'Al-Siddiq', 'specialization': 'Hadith Studies'},
            {'first_name': 'Hassan', 'last_name': 'Al-Basri', 'specialization': 'Fiqh'},
            
            # Conventional Subjects Teachers
            {'first_name': 'Sarah', 'last_name': 'Johnson', 'specialization': 'Mathematics'},
            {'first_name': 'Michael', 'last_name': 'Brown', 'specialization': 'Science'},
            {'first_name': 'Emily', 'last_name': 'Davis', 'specialization': 'English Language'},
            {'first_name': 'David', 'last_name': 'Wilson', 'specialization': 'History'},
            {'first_name': 'Lisa', 'last_name': 'Martinez', 'specialization': 'Geography'},
            {'first_name': 'James', 'last_name': 'Anderson', 'specialization': 'Computer Science'},
            {'first_name': 'Maria', 'last_name': 'Garcia', 'specialization': 'Art'},
            {'first_name': 'Robert', 'last_name': 'Taylor', 'specialization': 'Physical Education'},
        ]
        
        for teacher_data in teachers_data:
            email = f"{teacher_data['first_name'].lower()}.{teacher_data['last_name'].lower()}@miia.edu"
            
            user_data = {
                'email': email,
                'username': email.split('@')[0],
                'first_name': teacher_data['first_name'],
                'last_name': teacher_data['last_name'],
                'role': 'teacher',
                'is_active': True,
                'password': 'Teacher@123456'
            }
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.created_objects[f'teacher_{user.email}'] = user
                self.created_objects[f'teacher_{user.email}_spec'] = teacher_data['specialization']
    
    def _create_student_users(self):
        """Create students aged 7-15"""
        first_names_islamic = [
            'Muhammad', 'Abdullah', 'Omar', 'Ali', 'Hassan', 'Hussein',
            'Fatima', 'Aisha', 'Maryam', 'Zainab', 'Khadija', 'Sofia'
        ]
        first_names_conventional = [
            'Alex', 'Emma', 'Noah', 'Olivia', 'Liam', 'Ava', 'Ethan', 'Sophia'
        ]
        last_names = [
            'Abdullah', 'Al-Rahman', 'Al-Malik', 'Hassan', 'Ibrahim',
            'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson'
        ]
        
        # Create students for each grade level
        for grade in range(2, 11):  # Grade 2 through 10 (ages 7-15)
            students_per_grade = 8  # 8 students per grade
            
            for i in range(students_per_grade):
                # Mix Islamic and conventional names
                if i % 2 == 0:
                    first_name = self.random_choice(first_names_islamic)
                else:
                    first_name = self.random_choice(first_names_conventional)
                
                last_name = self.random_choice(last_names)
                email = f"{first_name.lower()}.{last_name.lower()}{self.random_int(1, 100)}@student.miia.edu"
                
                # Calculate age based on grade (Grade 2 = 7-8 years)
                current_year = datetime.now().year
                birth_year = current_year - (grade + 5)  # Grade 2 = 7 years old
                birth_month = self.random_int(1, 12)
                birth_day = self.random_int(1, 28)
                date_of_birth = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
                
                user_data = {
                    'email': email,
                    'username': email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'student',
                    'is_active': True,
                    'password': 'Student@123456'
                }
                
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults=user_data
                )
                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    self.created_objects[f'student_{user.email}'] = {
                        'user': user,
                        'grade': grade,
                        'date_of_birth': date_of_birth
                    }
    
    def _create_parent_users(self):
        """Create parent users for students"""
        parent_names = [
            ('Muhammad', 'Abdullah'), ('Ahmed', 'Hassan'), ('Omar', 'Ibrahim'),
            ('Khalid', 'Al-Rahman'), ('Yusuf', 'Ali'), ('Bilal', 'Malik'),
            ('John', 'Smith'), ('Robert', 'Johnson'), ('David', 'Williams'),
            ('James', 'Brown'), ('Michael', 'Davis'), ('William', 'Wilson')
        ]
        
        for i in range(40):
            first_name, last_name = self.random_choice(parent_names)
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            
            user_data = {
                'email': email,
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'role': 'parent',
                'is_active': True,
                'password': 'Parent@123456'
            }
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.created_objects[f'parent_{user.email}'] = user
    
    def _create_staff_users(self):
        """Create staff users"""
        staff_data = [
            {'first_name': 'Sarah', 'last_name': 'Miller', 'department': 'Admissions', 'position': 'Admissions Officer'},
            {'first_name': 'John', 'last_name': 'Taylor', 'department': 'Finance', 'position': 'Finance Officer'},
            {'first_name': 'Lisa', 'last_name': 'Anderson', 'department': 'HR', 'position': 'HR Manager'},
            {'first_name': 'David', 'last_name': 'Thomas', 'department': 'IT', 'position': 'IT Support'},
            {'first_name': 'Fatima', 'last_name': 'Hassan', 'department': 'Student Affairs', 'position': 'Student Counselor'},
            {'first_name': 'Omar', 'last_name': 'Farooq', 'department': 'Library', 'position': 'Librarian'},
        ]
        
        for staff_data_item in staff_data:
            email = f"{staff_data_item['first_name'].lower()}.{staff_data_item['last_name'].lower()}@miia.edu"
            
            user_data = {
                'email': email,
                'username': email.split('@')[0],
                'first_name': staff_data_item['first_name'],
                'last_name': staff_data_item['last_name'],
                'role': 'staff',
                'is_active': True,
                'password': 'Staff@123456'
            }
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.created_objects[f'staff_{user.email}'] = {
                    'user': user,
                    'department': staff_data_item['department'],
                    'position': staff_data_item['position']
                }
    
    def _create_teacher_profiles(self):
        """Create teacher profiles"""
        for user in User.objects.filter(role='teacher'):
            if not hasattr(user, 'teacher_profile'):
                teacher = Teacher.objects.create(
                    user=user,
                    employee_id=f"TCH{str(user.id).replace('-', '')[:8].upper()}",
                    qualification=self.random_choice(['M.Ed', 'B.Ed', 'M.A. Islamic Studies', 'B.A. Arabic', 'PhD']),
                    specialization=self.created_objects.get(f'teacher_{user.email}_spec', 'Islamic Studies'),
                    joining_date=self.random_date(start_date=datetime.now() - timedelta(days=365*5))
                )
                self.created_objects[f'teacher_profile_{user.email}'] = teacher
    
    def _create_student_profiles(self):
        """Create student profiles"""
        for student_data in self.created_objects.values():
            if isinstance(student_data, dict) and 'user' in student_data and student_data['user'].role == 'student':
                user = student_data['user']
                if not hasattr(user, 'student_profile'):
                    student = Student.objects.create(
                        user=user,
                        student_id=f"STU{str(user.id).replace('-', '')[:8].upper()}",
                        enrollment_date=self.random_date(start_date=datetime.now() - timedelta(days=365*2)),
                        date_of_birth=student_data.get('date_of_birth'),
                        guardian_name=f"{self.random_choice(['Muhammad', 'Ahmed', 'Abdullah', 'John', 'Robert'])} {self.random_choice(['Abdullah', 'Hassan', 'Smith', 'Johnson'])}",
                        guardian_phone=self.random_phone(),
                        guardian_relationship=self.random_choice(['father', 'mother', 'guardian'])
                    )
                    self.created_objects[f'student_profile_{user.email}'] = student
    
    def _create_parent_profiles(self):
        """Create parent profiles and link to students"""
        parents = list(User.objects.filter(role='parent'))
        students = list(Student.objects.all())
        
        for i, parent in enumerate(parents):
            if not hasattr(parent, 'parent_profile'):
                parent_profile = Parent.objects.create(
                    user=parent,
                    occupation=self.random_choice(['Engineer', 'Doctor', 'Teacher', 'Business Owner', 'Government Officer', 'Imam']),
                    relationship=self.random_choice(['father', 'mother', 'guardian']),
                    phone=self.random_phone(),
                    address=self.fake.address(),
                )
                self.created_objects[f'parent_profile_{parent.email}'] = parent_profile
                
                # Link 1-3 students to each parent
                num_children = self.random_int(1, 3)
                for _ in range(min(num_children, len(students))):
                    if students:
                        student = students.pop(0)
                        parent_profile.children.add(student)
    
    def _create_staff_profiles(self):
        """Create staff profiles"""
        for staff_data in self.created_objects.values():
            if isinstance(staff_data, dict) and 'user' in staff_data and staff_data['user'].role == 'staff':
                user = staff_data['user']
                if not hasattr(user, 'staff_profile'):
                    staff = Staff.objects.create(
                        user=user,
                        staff_id=f"STF{str(user.id).replace('-', '')[:8].upper()}",
                        department=staff_data['department'],
                        position=staff_data['position'],
                        joining_date=self.random_date(start_date=datetime.now() - timedelta(days=365*2))
                    )
                    self.created_objects[f'staff_profile_{user.email}'] = staff
    
    def _create_applications(self):
        """Create applications for parents"""
        parents = User.objects.filter(role='parent')
        
        for parent in parents:
            # Create one application per parent
            application, created = Application.objects.get_or_create(
                applicant=parent,
                defaults={
                    'status': self.random_choice(['submitted', 'under_review', 'approved']),
                    'current_step': 6,
                  
                    'submitted_at': timezone.now() - timedelta(days=self.random_int(1, 30))
                }
            )
            if created:
                self.created_objects[f'application_{parent.email}'] = application