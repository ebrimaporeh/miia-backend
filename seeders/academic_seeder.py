# seeders/academic_seeder.py
from datetime import datetime, timedelta
from django.utils import timezone
from apps.academics.models import (
    AcademicYear, Term, Subject, Course, CourseMaterial, 
    CourseAnnouncement, Enrollment
)
from apps.accounts.models import User, Teacher, Student, GradeLevel
from .base_seeder import BaseSeeder

class AcademicSeeder(BaseSeeder):
    """Seeder for academic data - Islamic School Focus (Grades 2-10, ages 7-15)"""
    
    def seed(self):
        print("  📅 Creating academic years...")
        self._create_academic_years()
        
        print("  📚 Creating subjects...")
        self._create_subjects()
        
        print("  📝 Creating terms...")
        self._create_terms()
        
        print("  🏫 Creating courses...")
        self._create_courses()
        
        print("  📝 Creating enrollments...")
        self._create_enrollments()
        
        print("  📄 Creating course materials...")
        self._create_course_materials()
        
        print("  📢 Creating course announcements...")
        self._create_course_announcements()
    
    def _create_academic_years(self):
        """Create academic years"""
        current_year = datetime.now().year
        academic_years = [
            {
                'name': f'{current_year-2}-{current_year-1}',
                'start_date': f'{current_year-2}-09-01',
                'end_date': f'{current_year-1}-06-30',
                'is_current': False
            },
            {
                'name': f'{current_year-1}-{current_year}',
                'start_date': f'{current_year-1}-09-01',
                'end_date': f'{current_year}-06-30',
                'is_current': True
            },
            {
                'name': f'{current_year}-{current_year+1}',
                'start_date': f'{current_year}-09-01',
                'end_date': f'{current_year+1}-06-30',
                'is_current': False
            },
        ]
        
        for year_data in academic_years:
            academic_year, created = AcademicYear.objects.get_or_create(
                name=year_data['name'],
                defaults=year_data
            )
            if created:
                self.created_objects[f'academic_year_{year_data["name"]}'] = academic_year
    
    def _create_terms(self):
        """Create terms for the current academic year"""
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        if current_academic_year:
            terms_data = [
                {
                    'name': 'Term 1',
                    'term_type': 'term1',
                    'start_date': current_academic_year.start_date,
                    'end_date': current_academic_year.start_date + timedelta(days=90),
                    'is_current': True
                },
                {
                    'name': 'Term 2',
                    'term_type': 'term2',
                    'start_date': current_academic_year.start_date + timedelta(days=91),
                    'end_date': current_academic_year.start_date + timedelta(days=180),
                    'is_current': False
                },
                {
                    'name': 'Term 3',
                    'term_type': 'term3',
                    'start_date': current_academic_year.start_date + timedelta(days=181),
                    'end_date': current_academic_year.end_date,
                    'is_current': False
                },
            ]
            
            for term_data in terms_data:
                term, created = Term.objects.get_or_create(
                    academic_year=current_academic_year,
                    term_type=term_data['term_type'],
                    defaults=term_data
                )
                if created:
                    self.created_objects[f'term_{term.term_type}'] = term
    
    def _create_subjects(self):
        """Create subjects for Islamic School (Grades 2-10)"""
        subjects_data = [
            # Islamic Core Subjects
            {
                'name': 'Quran & Tajweed',
                'code': 'QRN101',
                'category': 'quran',
                'description': 'Quran recitation with proper Tajweed rules',
                'is_islamic': True,
                'requires_memorization': True
            },
            {
                'name': 'Islamic Studies',
                'code': 'ISL101',
                'category': 'aqeedah',
                'description': 'Islamic beliefs, practices, and values',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Arabic Language',
                'code': 'ARB101',
                'category': 'arabic',
                'description': 'Arabic reading, writing, and comprehension',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Hadith Studies',
                'code': 'HAD101',
                'category': 'seerah',
                'description': 'Study of Prophet Muhammad\'s sayings',
                'is_islamic': True,
                'requires_memorization': True
            },
            {
                'name': 'Seerah (Prophet\'s Biography)',
                'code': 'SIR101',
                'category': 'seerah',
                'description': 'Life of Prophet Muhammad (PBUH)',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Fiqh (Islamic Jurisprudence)',
                'code': 'FIQ101',
                'category': 'fiqh',
                'description': 'Islamic rulings on worship and daily life',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Islamic History',
                'code': 'HIS101',
                'category': 'islamic_history',
                'description': 'History of Islamic civilization',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Adab (Islamic Ethics)',
                'code': 'ADB101',
                'category': 'adab',
                'description': 'Islamic manners and character building',
                'is_islamic': True,
                'requires_memorization': True
            },
            
            # Core Academic Subjects
            {
                'name': 'Mathematics',
                'code': 'MTH101',
                'category': 'mathematics',
                'description': 'Mathematics fundamentals',
                'is_islamic': False,
                'requires_memorization': False
            },
            {
                'name': 'English Language',
                'code': 'ENG101',
                'category': 'english',
                'description': 'English reading, writing, and grammar',
                'is_islamic': False,
                'requires_memorization': False
            },
            {
                'name': 'Science',
                'code': 'SCI101',
                'category': 'science',
                'description': 'General science concepts',
                'is_islamic': False,
                'requires_memorization': False
            },
            {
                'name': 'Social Studies',
                'code': 'SOC101',
                'category': 'social_studies',
                'description': 'Social studies and civic education',
                'is_islamic': False,
                'requires_memorization': False
            },
            {
                'name': 'Physical Education',
                'code': 'PED101',
                'category': 'physical_education',
                'description': 'Physical fitness and sports',
                'is_islamic': False,
                'requires_memorization': False
            },
            {
                'name': 'Islamic Arts & Calligraphy',
                'code': 'ART101',
                'category': 'arts',
                'description': 'Islamic art, calligraphy, and crafts',
                'is_islamic': True,
                'requires_memorization': False
            },
            {
                'name': 'Information Technology',
                'code': 'ICT101',
                'category': 'ict',
                'description': 'Basic computer skills and digital literacy',
                'is_islamic': False,
                'requires_memorization': False
            },
        ]
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults=subject_data
            )
            if created:
                self.created_objects[f'subject_{subject.code}'] = subject
    
    def _create_courses(self):
        """Create courses for each grade level"""
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_term = Term.objects.filter(academic_year=current_academic_year, is_current=True).first()
        
        # Get all teachers
        teachers = list(Teacher.objects.all())
        
        # Get or create grade levels for ages 7-15 (Grades 2-10)
        grade_levels = []
        for grade_num in range(2, 11):
            grade_level, created = GradeLevel.objects.get_or_create(
                level_number=grade_num,
                defaults={
                    'name': f'Grade {grade_num}',
                    'min_age': grade_num + 5,  # Grade 2 = age 7, Grade 3 = age 8, etc.
                    'max_age': grade_num + 6,
                    'is_active': True,
                    'order': grade_num
                }
            )
            grade_levels.append(grade_level)
            if created:
                self.created_objects[f'grade_level_{grade_num}'] = grade_level
        
        # Subjects to create courses for
        subjects = list(Subject.objects.all())
        
        # Course title templates
        course_titles = {
            'QRN101': ['Quran Recitation', 'Tajweed Rules', 'Quran Memorization'],
            'ISL101': ['Islamic Beliefs', 'Islamic Practices', 'Islamic Values'],
            'ARB101': ['Arabic Reading', 'Arabic Writing', 'Arabic Conversation'],
            'HAD101': ['40 Hadith', 'Hadith Collection', 'Hadith Explanation'],
            'SIR101': ['Prophet\'s Life', 'Companions Stories', 'Islamic Heroes'],
            'FIQ101': ['Worship Rules', 'Daily Fiqh', 'Islamic Transactions'],
            'HIS101': ['Islamic Civilization', 'Golden Age', 'Modern History'],
            'ADB101': ['Islamic Manners', 'Character Building', 'Etiquette'],
            'MTH101': ['Basic Math', 'Advanced Math', 'Problem Solving'],
            'ENG101': ['Grammar', 'Reading Comprehension', 'Creative Writing'],
            'SCI101': ['General Science', 'Biology Basics', 'Physics Fundamentals'],
            'SOC101': ['World History', 'Geography', 'Civics'],
            'PED101': ['Physical Fitness', 'Team Sports', 'Health Education'],
            'ART101': ['Islamic Calligraphy', 'Geometric Patterns', 'Crafts'],
            'ICT101': ['Computer Basics', 'Digital Skills', 'Programming Fundamentals'],
        }
        
        course_counter = 1
        for grade_level in grade_levels:
            for subject in subjects:
                # Only create courses for appropriate grade levels
                # Islamic subjects for all grades, math/science for older grades
                if subject.category in ['mathematics', 'science'] and grade_level.level_number < 3:
                    continue  # Skip advanced math/science for very young grades
                
                # Find a teacher who can teach this subject
                teacher = None
                for t in teachers:
                    if subject.name in t.specialization or t.specialization in subject.name:
                        teacher = t
                        break
                
                if not teacher and teachers:
                    teacher = self.random_choice(teachers)
                
                if teacher:
                    # Get title suggestions
                    title_options = course_titles.get(subject.code, [subject.name])
                    title = f"{self.random_choice(title_options)} - {grade_level.name}"
                    
                    # Generate schedule based on subject type
                    schedule = self._generate_schedule(subject)
                    
                    course_code = f"{subject.code}-{grade_level.level_number}{self.random_choice(['A', 'B'])}"
                    
                    course_data = {
                        'title': title,
                        'code': course_code,
                        'description': f"{subject.description} for {grade_level.name} students.",
                        'subject': subject,
                        'instructor': teacher,
                        'grade_level': grade_level,
                        'credits': subject.category in ['quran', 'arabic', 'mathematics', 'english'] and 4 or 2,
                        'level': self.random_choice(['beginner', 'intermediate', 'advanced']),
                        'schedule': schedule,
                        'duration': '16 weeks',
                        'room': f"RM-{self.random_int(100, 300)}",
                        'max_students': self.random_int(20, 30),
                        'current_students': 0,
                        'start_date': current_academic_year.start_date,
                        'end_date': current_academic_year.end_date,
                        'academic_year': current_academic_year,
                        'term': current_term,
                        'prerequisites': [],
                        'objectives': self._generate_objectives(subject, grade_level),
                        'status': self.random_choice(['active', 'active', 'active', 'upcoming']),
                        'color': self._get_subject_color(subject.category),
                    }
                    
                    course, created = Course.objects.get_or_create(
                        code=course_code,
                        defaults=course_data
                    )
                    
                    if created:
                        self.created_objects[f'course_{course.code}'] = course
                        course_counter += 1
    
    def _generate_schedule(self, subject):
        """Generate schedule based on subject type"""
        days = []
        if subject.is_islamic:
            # Islamic subjects taught daily
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Sun']
            time = '08:00-09:30'
        else:
            # Conventional subjects 2-3 times a week
            days = self.random_choice([
                ['Mon', 'Wed'],
                ['Tue', 'Thu'],
                ['Mon', 'Wed', 'Fri'],
                ['Tue', 'Thu', 'Sun']
            ])
            time = self.random_choice(['09:30-11:00', '11:00-12:30', '13:30-15:00'])
        
        return f"{'/'.join(days)} {time}"
    
    def _generate_objectives(self, subject, grade_level):
        """Generate learning objectives for a course"""
        base_objectives = [
            f"Understand key concepts of {subject.name}",
            f"Apply {subject.name} knowledge in practical situations",
            f"Develop critical thinking skills through {subject.name}",
            f"Demonstrate proficiency in {subject.name}",
        ]
        
        if subject.is_islamic:
            base_objectives.append(f"Connect {subject.name} teachings to daily life")
            base_objectives.append(f"Memorize important verses/hadith related to {subject.name}")
        
        return base_objectives
    
    def _get_subject_color(self, category):
        """Get color for subject based on category"""
        colors = {
            'quran': '#2E7D32',  # Green
            'arabic': '#1565C0',  # Blue
            'islamic_history': '#6A1B9A',  # Purple
            'fiqh': '#C2185B',  # Pink
            'seerah': '#F57C00',  # Orange
            'adab': '#8D6E63',  # Brown
            'mathematics': '#D32F2F',  # Red
            'english': '#1976D2',  # Light Blue
            'science': '#388E3C',  # Light Green
            'social_studies': '#FBC02D',  # Yellow
            'physical_education': '#00796B',  # Teal
            'arts': '#E91E63',  # Hot Pink
            'ict': '#9C27B0',  # Deep Purple
        }
        return colors.get(category, '#757575')  # Grey default
    
    def _create_enrollments(self):
        """Enroll students in courses"""
        students = list(Student.objects.all())
        courses = list(Course.objects.filter(status='active'))
        
        enrollment_count = 0
        for student in students:
            # Determine grade level for student
            grade_level = None
            for gl in GradeLevel.objects.all():
                if student.age and gl.min_age <= student.age <= gl.max_age:
                    grade_level = gl
                    break
            
            if not grade_level:
                continue
            
            # Get courses for this grade level
            available_courses = [c for c in courses if c.grade_level == grade_level]
            
            # Enroll in 4-6 courses per student
            num_courses = min(self.random_int(4, 6), len(available_courses))
            selected_courses = self.random_choice(available_courses, k=num_courses)
            
            for course in selected_courses:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'status': 'enrolled',
                        'progress': self.random_int(10, 95),
                        'last_activity': timezone.now() - timedelta(days=self.random_int(0, 7))
                    }
                )
                if created:
                    enrollment_count += 1
                    # Update course current_students count
                    course.current_students += 1
                    course.save()
                    self.created_objects[f'enrollment_{student.user.email}_{course.code}'] = enrollment
        
        print(f"    Created {enrollment_count} enrollments")
    
    def _create_course_materials(self):
        """Create course materials for each course"""
        courses = Course.objects.all()
        material_types = ['pdf', 'doc', 'ppt', 'video', 'link']
        
        material_count = 0
        for course in courses:
            # Create 3-8 materials per course
            num_materials = self.random_int(3, 8)
            
            for i in range(num_materials):
                material_type = self.random_choice(material_types)
                material_data = {
                    'course': course,
                    'name': f"{course.title} - {self._get_material_name(material_type, i)}",
                    'type': material_type,
                    'uploaded_by': course.instructor.user if course.instructor else None,
                }
                
                if material_type in ['pdf', 'doc', 'ppt']:
                    material_data['size'] = f"{self.random_float(0.5, 15, 1)} MB"
                    material_data['file'] = f"course_materials/{course.code}/material_{i}.pdf"
                else:
                    material_data['url'] = f"https://example.com/courses/{course.code}/resource/{i}"
                
                material, created = CourseMaterial.objects.get_or_create(
                    course=course,
                    name=material_data['name'],
                    defaults=material_data
                )
                if created:
                    material_count += 1
                    self.created_objects[f'material_{course.code}_{i}'] = material
        
        print(f"    Created {material_count} course materials")
    
    def _get_material_name(self, material_type, index):
        """Generate material name based on type"""
        names = {
            'pdf': ['Introduction', 'Chapter', 'Guide', 'Worksheet', 'Notes'],
            'doc': ['Lesson Plan', 'Activity Sheet', 'Assignment', 'Reading Material'],
            'ppt': ['Presentation', 'Slides', 'Lecture Notes', 'Visual Guide'],
            'video': ['Video Tutorial', 'Lecture Recording', 'Explanation Video'],
            'link': ['External Resource', 'Reference Link', 'Additional Reading'],
        }
        return self.random_choice(names.get(material_type, ['Resource']))
    
    def _create_course_announcements(self):
        """Create announcements for each course"""
        courses = Course.objects.all()
        priorities = ['low', 'medium', 'high']
        
        announcement_count = 0
        for course in courses:
            # Create 2-5 announcements per course
            num_announcements = self.random_int(2, 5)
            
            for i in range(num_announcements):
                announcement_data = {
                    'course': course,
                    'title': self._get_announcement_title(i),
                    'content': self._get_announcement_content(course),
                    'author': course.instructor.user if course.instructor else None,
                    'priority': self.random_choice(priorities),
                    'attachments': []
                }
                
                announcement, created = CourseAnnouncement.objects.get_or_create(
                    course=course,
                    title=announcement_data['title'],
                    defaults=announcement_data
                )
                if created:
                    announcement_count += 1
                    self.created_objects[f'announcement_{course.code}_{i}'] = announcement
        
        print(f"    Created {announcement_count} course announcements")
    
    def _get_announcement_title(self, index):
        """Generate announcement title"""
        titles = [
            'Welcome to the Course!',
            'Important Update',
            'Assignment Due Date',
            'Class Schedule Change',
            'Exam Preparation Tips',
            'Reminder: Upcoming Quiz',
            'New Resources Available',
            'Holiday Schedule',
            'Parent-Teacher Meeting',
            'Course Feedback Request'
        ]
        return self.random_choice(titles)
    
    def _get_announcement_content(self, course):
        """Generate announcement content"""
        templates = [
            f"Dear students, welcome to {course.title}. I hope you're excited to learn about {course.subject.name}. Please review the course materials.",
            f"Important announcement for {course.title}: There will be an assessment next week. Please prepare accordingly.",
            f"Reminder: The deadline for the assignment in {course.title} is approaching. Submit on time.",
            f"Due to upcoming holidays, our {course.title} class schedule has been adjusted. Please check the updated timetable.",
            f"Great job on the recent quiz in {course.title}! Keep up the good work.",
            f"New study resources have been added for {course.title}. Check them out in the materials section.",
        ]
        return self.random_choice(templates)