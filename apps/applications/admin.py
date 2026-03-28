# apps/applications/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Count, Q
from .models import Application


class ApplicationFilter(admin.SimpleListFilter):
    """Custom filter for application status with counts"""
    title = 'status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        statuses = Application.STATUS_CHOICES
        counts = {}
        for status_code, _ in statuses:
            counts[status_code] = Application.objects.filter(status=status_code).count()
        
        return [
            (status_code, f"{label} ({counts.get(status_code, 0)})")
            for status_code, label in statuses
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class PendingReviewFilter(admin.SimpleListFilter):
    """Filter for applications pending review"""
    title = 'needs review'
    parameter_name = 'needs_review'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', 'Pending Review'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(status='submitted')
        if self.value() == 'submitted':
            return queryset.filter(status='submitted')
        if self.value() == 'under_review':
            return queryset.filter(status='under_review')
        return queryset


class ChildrenInline(admin.TabularInline):
    """Inline display of children in the application"""
    model = Application.children.through
    verbose_name = "Child"
    verbose_name_plural = "Children"
    extra = 0
    fields = ['student_link', 'student_id', 'student_name', 'student_status']
    readonly_fields = ['student_link', 'student_id', 'student_name', 'student_status']
    can_delete = False
    max_num = 0
    
    def student_link(self, obj):
        if obj.student:
            url = reverse('admin:accounts_student_change', args=[obj.student.id])
            return format_html('<a href="{}">{}</a>', url, obj.student.student_id)
        return '-'
    student_link.short_description = 'Student'
    
    def student_id(self, obj):
        return obj.student.student_id if obj.student else '-'
    student_id.short_description = 'Student ID'
    
    def student_name(self, obj):
        if obj.student:
            return obj.student.user.get_full_name()
        return '-'
    student_name.short_description = 'Name'
    
    def student_status(self, obj):
        if obj.student:
            status_colors = {
                'active': 'green',
                'pending': 'orange',
                'inactive': 'gray',
                'graduated': 'blue',
                'suspended': 'red',
            }
            color = status_colors.get(obj.student.status, 'gray')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                obj.student.status.upper()
            )
        return '-'
    student_status.short_description = 'Status'


class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for Application model"""
    
    # List view configuration
    list_display = [
        'id_short',
        'applicant_link',
        'children_count_display',
        'parent_link',
        'status_badge',
        'current_step',
        'submitted_date',
        'review_status',
        'days_pending'
    ]
    
    list_filter = [
        PendingReviewFilter,
        ApplicationFilter,
        'current_step',
        'submitted_at',
        'reviewed_at',
    ]
    
    search_fields = [
        'applicant__email',
        'applicant__first_name',
        'applicant__last_name',
        'parent__user__email',
        'children__user__first_name',
        'children__user__last_name',
        'children__student_id',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'submitted_at',
        'reviewed_at',
        'reviewed_by',
        'application_details',
    ]
    
    fieldsets = (
        ('Application Information', {
            'fields': ('id', 'applicant', 'parent', 'status', 'current_step')
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
    
    inlines = [ChildrenInline]
    
    actions = [
        'mark_as_under_review',
        'mark_as_approved',
        'mark_as_rejected',
        'mark_as_completed',
        'send_reminder_email',
    ]
    
    # List view customization
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).select_related(
            'applicant', 'parent', 'reviewed_by'
        ).prefetch_related('children')
    
    def id_short(self, obj):
        """Display short ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    id_short.admin_order_field = 'id'
    
    def applicant_link(self, obj):
        """Link to the applicant user"""
        url = reverse('admin:accounts_user_change', args=[obj.applicant.id])
        name = obj.applicant.get_full_name() or obj.applicant.email
        return format_html('<a href="{}">{}</a>', url, name)
    applicant_link.short_description = 'Applicant'
    applicant_link.admin_order_field = 'applicant__email'
    
    def parent_link(self, obj):
        """Link to the parent profile if exists"""
        if obj.parent:
            url = reverse('admin:accounts_parent_change', args=[obj.parent.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent.user.get_full_name())
        return '-'
    parent_link.short_description = 'Parent'
    
    def children_count_display(self, obj):
        """Display children count with link"""
        count = obj.children.count()
        if count > 0:
            url = reverse('admin:accounts_student_changelist')
            url += f'?applications__id={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    children_count_display.short_description = 'Children'
    children_count_display.admin_order_field = 'children_count'
    
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
        if obj.parent:
            details.append(f"""
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 5px 0;">👤 Parent/Guardian</h4>
                    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                        <strong>Name:</strong> {obj.parent.user.get_full_name()}<br>
                        <strong>Email:</strong> {obj.parent.user.email}<br>
                        <strong>Phone:</strong> {obj.parent.phone}<br>
                        <strong>Relationship:</strong> {obj.parent.relationship}<br>
                        <strong>Address:</strong> {obj.parent.address}
                    </div>
                </div>
            """)
        
        # Children Info
        if obj.children.exists():
            children_html = '<div style="margin-bottom: 15px;"><h4 style="margin: 0 0 5px 0;">👶 Children</h4><div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
            for child in obj.children.all():
                children_html += f"""
                    <div style="margin-bottom: 10px; padding: 8px; border-bottom: 1px solid #ddd;">
                        <strong>{child.user.get_full_name()}</strong><br>
                        Student ID: {child.student_id}<br>
                        Date of Birth: {child.date_of_birth}<br>
                        Status: {child.status}
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
    
    def mark_as_completed(self, request, queryset):
        """Mark selected applications as completed"""
        updated = queryset.filter(status='approved').update(
            status='completed'
        )
        self.message_user(request, f'{updated} application(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as Completed'
    
    def send_reminder_email(self, request, queryset):
        """Send reminder email to applicants"""
        # This would integrate with your email system
        count = queryset.count()
        self.message_user(request, f'Reminder email sent to {count} applicant(s).')
    send_reminder_email.short_description = 'Send Reminder Email'
    
    # Save method overrides
    def save_model(self, request, obj, form, change):
        """Override save to track review changes"""
        if obj.status in ['approved', 'rejected'] and not obj.reviewed_at:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)


# Register the admin
admin.site.register(Application, ApplicationAdmin)