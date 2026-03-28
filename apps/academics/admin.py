# apps/academics/admin.py
from django.contrib import admin
from .models import (
    AcademicYear, Term, Subject, Course, 
    CourseMaterial, CourseAnnouncement, Enrollment
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-start_date',)

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'term_type', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'is_current', 'term_type')
    search_fields = ('name', 'academic_year__name')
    ordering = ('academic_year', 'start_date')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_islamic', 'requires_memorization', 'is_active')
    list_filter = ('category', 'is_islamic', 'is_active', 'requires_memorization')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'category', 'description')
        }),
        ('Islamic Studies', {
            'fields': ('is_islamic', 'requires_memorization'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 1
    fields = ('name', 'type', 'file', 'url', 'size')

class CourseAnnouncementInline(admin.TabularInline):
    model = CourseAnnouncement
    extra = 0
    fields = ('title', 'priority', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'subject', 'instructor_name', 'grade_level', 
                   'status', 'current_students', 'max_students')
    list_filter = ('status', 'subject__category', 'grade_level', 'academic_year', 'term')
    search_fields = ('code', 'title', 'description', 'instructor__user__first_name')
    ordering = ('code',)
    filter_horizontal = ()  # Remove if you add any ManyToMany fields
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'code', 'description', 'subject', 'grade_level')
        }),
        ('Instructor & Schedule', {
            'fields': ('instructor', 'schedule', 'duration', 'room')
        }),
        ('Academic Details', {
            'fields': ('credits', 'level', 'prerequisites', 'objectives')
        }),
        ('Dates & Enrollment', {
            'fields': ('start_date', 'end_date', 'academic_year', 'term', 
                      'max_students', 'current_students')
        }),
        ('Status & UI', {
            'fields': ('status', 'color')
        }),
    )
    
    inlines = [CourseMaterialInline, CourseAnnouncementInline]
    
    def instructor_name(self, obj):
        return obj.instructor.user.get_full_name() if obj.instructor else "-"
    instructor_name.short_description = 'Instructor'
    instructor_name.admin_order_field = 'instructor__user__first_name'

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'type', 'uploaded_by', 'uploaded_at')
    list_filter = ('type', 'course__subject__category')
    search_fields = ('name', 'course__title', 'course__code')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)

@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'priority', 'created_at')
    list_filter = ('priority', 'course__subject__category')
    search_fields = ('title', 'content', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'student_id', 'course_code', 'course_title', 
                   'enrollment_date', 'status', 'progress')
    list_filter = ('status', 'course__subject__category', 'enrollment_date')
    search_fields = ('student__user__first_name', 'student__user__last_name', 
                    'student__student_id', 'course__code', 'course__title')
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Course Information', {
            'fields': ('course',)
        }),
        ('Enrollment Details', {
            'fields': ('status', 'enrollment_date', 'progress', 'last_activity')
        }),
        ('Grades', {
            'fields': ('final_grade', 'final_score'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student Name'
    student_name.admin_order_field = 'student__user__first_name'
    
    def student_id(self, obj):
        return obj.student.student_id
    student_id.short_description = 'Student ID'
    student_id.admin_order_field = 'student__student_id'
    
    def course_code(self, obj):
        return obj.course.code
    course_code.short_description = 'Course Code'
    course_code.admin_order_field = 'course__code'
    
    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = 'Course Title'
    course_title.admin_order_field = 'course__title'