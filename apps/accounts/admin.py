# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    User, Teacher, Student, Parent, Staff, 
    GradeLevel, StudentDocument, StudentNote
)


class ChildrenInline(admin.TabularInline):
    """Inline display of children for a parent"""
    model = Student
    fields = ('student_id', 'name_link', 'status', 'enrollment_date')
    readonly_fields = ('student_id', 'name_link', 'status', 'enrollment_date')
    extra = 0
    can_delete = False
    max_num = 0
    verbose_name = "Child"
    verbose_name_plural = "Children"
    
    def name_link(self, obj):
        # obj is a Student instance
        url = reverse('admin:accounts_student_change', args=[obj.user.id])  # Student uses user.id
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    name_link.short_description = 'Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'role', 'is_active', 'phone')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'username', 'phone', 'password1', 'password2'),
        }),
    )


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'level_number', 'display_name', 'min_age', 'max_age', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'display_name')
    ordering = ('level_number',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'level_number', 'display_name')
        }),
        ('Age Range', {
            'fields': ('min_age', 'max_age')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )


class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 0
    fields = ('document_type', 'title', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class StudentNoteInline(admin.TabularInline):
    model = StudentNote
    extra = 0
    fields = ('author', 'content', 'is_private', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'email', 'parent_link', 'status', 'performance', 'enrollment_date')
    list_filter = ('status', 'performance', 'gender')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'user__email')
    ordering = ('-enrollment_date',)
    readonly_fields = ('created_at', 'updated_at', 'last_active')
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Student Information', {
            'fields': ('student_id', 'date_of_birth', 'gender',)
        }),
        ('Academic Information', {
            'fields': ('enrollment_date', 'graduation_date', 'status', 'performance', 'department')
        }),
        ('Parent/Guardian', {
            'fields': ('parent', 'guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Advisor', {
            'fields': ('advisor',)
        }),
        ('Medical Information', {
            'fields': ('has_allergies', 'allergy_details', 'medical_conditions'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('last_active', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StudentDocumentInline, StudentNoteInline]
    
    def name(self, obj):
        return obj.user.get_full_name()
    name.short_description = 'Name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def parent_link(self, obj):
        if obj.parent:
            # Parent uses user as primary key, so parent.id is actually parent.user.id
            # Or you can use parent.user.id directly
            url = reverse('admin:accounts_parent_change', args=[obj.parent.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent.user.get_full_name())
        return '-'
    parent_link.short_description = 'Parent'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'parent__user')


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type',)
    search_fields = ('title', 'student__user__first_name', 'student__student_id')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'author', 'is_private', 'created_at')
    list_filter = ('is_private',)
    search_fields = ('student__user__first_name', 'content', 'author__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'email', 'qualification', 'specialization', 'joining_date')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email')
    list_filter = ('qualification',)
    ordering = ('-joining_date',)
    readonly_fields = ('user',)
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('employee_id', 'qualification', 'specialization', 'joining_date')
        }),
    )
    
    def name(self, obj):
        return obj.user.get_full_name()
    name.short_description = 'Name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'relationship', 'phone', 'children_count', 'children_preview')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')
    list_filter = ('relationship',)
    inlines = [ChildrenInline]
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Parent Information', {
            'fields': ('occupation', 'relationship', 'phone', 'alternate_phone', 'address')
        }),
    )
    
    def name(self, obj):
        return obj.user.get_full_name()
    name.short_description = 'Name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = 'Children'
    
    def children_preview(self, obj):
        children = obj.children.all()[:3]
        if children.exists():
            names = [child.user.get_full_name() for child in children]
            result = ", ".join(names)
            if obj.children.count() > 3:
                result += f" (+{obj.children.count() - 3} more)"
            return result
        return "-"
    children_preview.short_description = 'Children Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('children__user')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'name', 'email', 'department', 'position', 'joining_date')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name', 'user__email', 'department')
    list_filter = ('department', 'position')
    ordering = ('-joining_date',)
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Staff Information', {
            'fields': ('staff_id', 'department', 'position', 'joining_date')
        }),
    )
    
    def name(self, obj):
        return obj.user.get_full_name()
    name.short_description = 'Name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'