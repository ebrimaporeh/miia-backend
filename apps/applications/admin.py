# apps/applications/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import Application, ApplicantParent, ApplicantChild


class ApplicantParentInline(admin.StackedInline):
    """Inline display of parent information in the application"""
    model = ApplicantParent
    can_delete = False
    extra = 0
    fields = (
        'full_name', 'email', 'phone', 'alternate_phone',
        'address', 'occupation', 'relationship'
    )
    # Remove readonly_fields to allow editing
    # readonly_fields = fields
    verbose_name = "Parent/Guardian Information"
    verbose_name_plural = "Parent/Guardian Information"


class ApplicantChildInline(admin.TabularInline):
    """Inline display of children in the application"""
    model = ApplicantChild
    extra = 0
    fields = (
        'first_name', 'last_name', 'date_of_birth', 'gender', 
        'has_allergies', 'allergy_details', 'medical_conditions'
    )
    # Remove readonly_fields to allow editing
    # readonly_fields = fields
    can_delete = True
    verbose_name = "Child"
    verbose_name_plural = "Children"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for Application model"""
    
    list_display = (
        'id_short', 'applicant_link', 'parent_name', 'children_count_display',
        'status_badge', 'submitted_date', 'review_status', 'days_pending'
    )
    
    list_filter = ['status', 'current_step', 'submitted_at']
    
    search_fields = [
        'applicant__email', 'applicant__first_name', 'applicant__last_name',
        'applicant_parent__full_name', 'applicant_parent__email'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'submitted_at', 'reviewed_at',
        'reviewed_by', 'application_details'
    ]
    
    fieldsets = (
        ('Application Information', {
            'fields': ('applicant', 'status', 'current_step')
        }),
        ('Terms & Conditions', {
            'fields': ('terms_accepted', 'privacy_accepted')
        }),
        ('Submission', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('application_details',),
            'classes': ('wide',)
        })
    )
    
    inlines = [ApplicantParentInline, ApplicantChildInline]
    
    actions = [
        'mark_as_under_review',
        'mark_as_approved',
        'mark_as_rejected',
        'send_reminder_email',
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).select_related(
            'applicant', 'applicant_parent', 'reviewed_by'
        ).prefetch_related('applicant_children')
    
    def id_short(self, obj):
        """Display short ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    id_short.admin_order_field = 'id'
    
    def applicant_link(self, obj):
        """Link to the applicant user"""
        if obj.applicant:
            url = reverse('admin:accounts_user_change', args=[obj.applicant.id])
            return format_html('<a href="{}">{}</a>', url, obj.applicant.email)
        return '-'
    applicant_link.short_description = 'Applicant'
    applicant_link.admin_order_field = 'applicant__email'
    
    def parent_name(self, obj):
        """Display parent name from applicant_parent"""
        if hasattr(obj, 'applicant_parent') and obj.applicant_parent:
            return obj.applicant_parent.full_name
        return '-'
    parent_name.short_description = 'Parent/Guardian'
    
    def children_count_display(self, obj):
        """Display children count"""
        count = obj.applicant_children.count()
        if count > 0:
            return format_html('<span style="font-weight: bold;">{}</span>', count)
        return '0'
    children_count_display.short_description = 'Children'
    
    def submitted_date(self, obj):
        """Display submitted date with icon"""
        if obj.submitted_at:
            days_ago = (timezone.now() - obj.submitted_at).days
            if days_ago <= 1:
                return format_html('<span style="color: green;">📅 Today</span>')
            elif days_ago <= 7:
                return format_html('<span style="color: orange;">📅 {} days ago</span>', days_ago)
            else:
                return format_html('<span style="color: red;">📅 {} days ago</span>', days_ago)
        return '-'
    submitted_date.short_description = 'Submitted'
    submitted_date.admin_order_field = 'submitted_at'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'draft': 'gray',
            'in_progress': 'blue',
            'submitted': 'orange',
            'under_review': 'purple',
            'approved': 'green',
            'rejected': 'red',
            'completed': 'teal',
        }
        
        status_labels = {
            'draft': '📄 Draft',
            'in_progress': '🔄 In Progress',
            'submitted': '⏳ Submitted',
            'under_review': '🔍 Under Review',
            'approved': '✅ Approved',
            'rejected': '❌ Rejected',
            'completed': '🎉 Completed',
        }
        
        color = status_colors.get(obj.status, 'gray')
        label = status_labels.get(obj.status, obj.status)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            label
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def review_status(self, obj):
        """Display review status"""
        if obj.reviewed_at:
            reviewer = obj.reviewed_by.get_full_name() if obj.reviewed_by else 'System'
            return format_html(
                '<span style="color: green;">✓ Reviewed by {}</span>',
                reviewer
            )
        return '<span style="color: gray;">⏳ Not reviewed yet</span>'
    review_status.short_description = 'Review'
    
    def days_pending(self, obj):
        """Calculate days since submission"""
        if obj.submitted_at and obj.status in ['submitted', 'under_review']:
            days = (timezone.now() - obj.submitted_at).days
            if days > 7:
                return format_html('<span style="color: red;">{} days ⚠️</span>', days)
            elif days > 3:
                return format_html('<span style="color: orange;">{} days</span>', days)
            return format_html('<span style="color: green;">{} days</span>', days)
        return '-'
    days_pending.short_description = 'Pending Days'
    
    def application_details(self, obj):
        """Display application details in a readable format"""
        details = []
        
        # Parent Info
        if hasattr(obj, 'applicant_parent') and obj.applicant_parent:
            parent = obj.applicant_parent
            details.append(f"""
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 5px 0;">👤 Parent/Guardian</h4>
                    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                        <strong>Name:</strong> {parent.full_name}<br>
                        <strong>Email:</strong> {parent.email}<br>
                        <strong>Phone:</strong> {parent.phone}<br>
                        <strong>Relationship:</strong> {parent.get_relationship_display()}<br>
                        <strong>Occupation:</strong> {parent.occupation or 'N/A'}<br>
                        <strong>Address:</strong> {parent.address}
                    </div>
                </div>
            """)
        
        # Children Info
        children = obj.applicant_children.all()
        if children.exists():
            children_html = '<div style="margin-bottom: 15px;"><h4 style="margin: 0 0 5px 0;">👶 Children</h4><div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
            for child in children:
                children_html += f"""
                    <div style="margin-bottom: 10px; padding: 8px; border-bottom: 1px solid #ddd;">
                        <strong>{child.first_name} {child.last_name}</strong><br>
                        Date of Birth: {child.date_of_birth}<br>
                        Gender: {child.get_gender_display()}<br>
                        Allergies: {'Yes' if child.has_allergies else 'No'}<br>
                        Medical Conditions: {child.medical_conditions or 'None'}
                    </div>
                """
            children_html += '</div></div>'
            details.append(children_html)
        
        # Terms
        details.append(f"""
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 5px 0;">📜 Terms & Conditions</h4>
                <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                    Terms Accepted: {'✅ Yes' if obj.terms_accepted else '❌ No'}<br>
                    Privacy Accepted: {'✅ Yes' if obj.privacy_accepted else '❌ No'}
                </div>
            </div>
        """)
        
        # Review Notes
        if obj.review_notes:
            details.append(f"""
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 5px 0;">📝 Review Notes</h4>
                    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {obj.review_notes}
                    </div>
                </div>
            """)
        
        # Rejection Reason
        if obj.rejection_reason:
            details.append(f"""
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 5px 0;">❌ Rejection Reason</h4>
                    <div style="background: #ffebee; padding: 10px; border-radius: 5px; color: #c62828;">
                        {obj.rejection_reason}
                    </div>
                </div>
            """)
        
        return mark_safe(''.join(details))
    application_details.short_description = 'Application Details'
    
    # Admin actions
    def mark_as_under_review(self, request, queryset):
        """Mark selected applications as under review"""
        updated = queryset.filter(status='submitted').update(
            status='under_review',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_as_under_review.short_description = 'Mark as Under Review'
    
    def mark_as_approved(self, request, queryset):
        """Approve selected applications"""
        updated = queryset.filter(status__in=['submitted', 'under_review']).update(
            status='approved',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} application(s) approved.')
    mark_as_approved.short_description = 'Approve Applications'
    
    def mark_as_rejected(self, request, queryset):
        """Reject selected applications"""
        updated = queryset.filter(status__in=['submitted', 'under_review']).update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} application(s) rejected.')
    mark_as_rejected.short_description = 'Reject Applications'
    
    def send_reminder_email(self, request, queryset):
        """Send reminder email to applicants"""
        count = queryset.count()
        self.message_user(request, f'Reminder email sent to {count} applicant(s).')
    send_reminder_email.short_description = 'Send Reminder Email'


@admin.register(ApplicantParent)
class ApplicantParentAdmin(admin.ModelAdmin):
    """Admin interface for ApplicantParent model"""
    list_display = ('full_name', 'email', 'phone', 'relationship', 'application_link')
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('relationship',)
    # Remove readonly_fields to allow editing
    # readonly_fields = ('application_link',)
    
    def application_link(self, obj):
        url = reverse('admin:applications_application_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.id)
    application_link.short_description = 'Application'


@admin.register(ApplicantChild)
class ApplicantChildAdmin(admin.ModelAdmin):
    """Admin interface for ApplicantChild model"""
    list_display = ('full_name', 'date_of_birth', 'gender', 'application_link')
    search_fields = ('first_name', 'last_name')
    list_filter = ('gender', 'has_allergies')
    # Remove readonly_fields to allow editing
    # readonly_fields = ('application_link',)
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def application_link(self, obj):
        url = reverse('admin:applications_application_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.id)
    application_link.short_description = 'Application'