from rest_framework import serializers
from task.models import Task
from .models import *
from django.utils import timezone




class CheckInOutSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=255, required=True)
    check_date = serializers.CharField(max_length=255, required=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    check_time = serializers.CharField(max_length=100, required=True)
    time_zone = serializers.CharField(max_length=100, required=True)

    def validate_location(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Location is required")
        return value
    
    def validate_check_date(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Check date is required")
        return value

    def validate_check_time(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Check time is required")
        return value

    def validate_time_zone(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Time zone is required")
        return value

    def validate(self, data):
        # For checkout, reason is mandatory
        if self.context.get('is_checkout', False):
            reason = data.get('reason')
            if not reason or str(reason).strip() == '':
                raise serializers.ValidationError({
                    "reason": "Reason is required for checkout"
                })
        return data
    



class BreakSerializer(serializers.Serializer):
    break_type = serializers.ChoiceField(
        choices=['lunch', 'coffee', 'stretch', 'other'],
        required=True
    )
    custom_break_type = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.CharField(required=True)  
    break_start_time = serializers.CharField(required=True) 
    location = serializers.CharField(required=True)
    date = serializers.CharField(required=True)

    def validate(self, data):
        # If break_type is 'other', custom_break_type is required
        if data.get('break_type') == 'other' and not data.get('custom_break_type'):
            raise serializers.ValidationError({
                "custom_break_type": "Custom break type is required when selecting 'Other'"
            })
        return data



class EndBreakSerializer(serializers.Serializer):
    break_end_time = serializers.CharField(required=True)
    location = serializers.CharField(required=True)
    date = serializers.CharField(required=True)
    end_reason = serializers.CharField(required=False, allow_blank=True)    





class CompanyAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAnnouncement
        fields = ['id', 'heading', 'description', 'date']    
    






class LeaveHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Leave
        fields = [
            'id',
            'category',
            'start_date',
            'status',
            'reason',
        ]
    


class LeaveDashboardSerializer(serializers.Serializer):
    # Top section - Days Left
    days_left = serializers.IntegerField()
    total_vacation_days = serializers.IntegerField()
    used_vacation_days = serializers.IntegerField()
    
    # Middle section - Leave counts
    leave_taken_this_month = serializers.IntegerField()
    annual_leave_taken = serializers.IntegerField()

    leave_requests = LeaveHistorySerializer(many=True)

    # Leave history (all leaves)
    leave_history = LeaveHistorySerializer(many=True)
    
    class Meta:
        fields = [
            'days_left',
            'total_vacation_days',
            'used_vacation_days',
            'leave_taken_this_month',
            'annual_leave_taken',
            'leave_requests',
            'leave_history'
        ]


import os
class LeaveCreateSerializer(serializers.ModelSerializer):
    category = serializers.ChoiceField(choices=Leave.LEAVE_CATEGORY_CHOICES)
    start_date = serializers.CharField(max_length=100, required=True)
    end_date = serializers.CharField(max_length=100, required=True)
    total_days = serializers.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        min_value=0.5
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    passport_required_from = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True
    )
    passport_required_to = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True
    )
    address_during_leave = serializers.CharField(
        required=False, 
        allow_blank=True
    )
    
    class Meta:
        model = Leave
        fields = [
            'category',
            'start_date',
            'end_date',
            'total_days',
            'reason',
            'passport_required_from',
            'passport_required_to',
            'address_during_leave',
            'attachment',
            'signature'
        ]
    
    def validate_total_days(self, value):
        """Validate that total_days is a positive number"""
        if value <= 0:
            raise serializers.ValidationError("Total days must be greater than 0")
        return value
    

    def validate_attachment(self, value):
        """Validate the attachment file"""
        if value:
            # Check file size (e.g., 5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("File size should not exceed 5MB.")
            
            # Check file extension
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}"
                )
        
        return value
    
    def validate_signature(self, value):
        """Validate the signature file"""
        if value:
            max_size = 2 * 1024 * 1024  # 2MB
            if value.size > max_size:
                raise serializers.ValidationError("Signature file size should not exceed 2MB.")
            
            # Check file extension for images
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file extension for signature. Allowed: {', '.join(valid_extensions)}"
                )
        
        return value




class DetailedLeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employeeId', read_only=True)
    approved_by_name = serializers.SerializerMethodField(read_only=True) 
    # File URLs
    attachment_url = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()

    
    class Meta:
        model = Leave
        fields = [
            # Basic info
            'id',
            'category',
            'start_date',
            'end_date',
            'total_days',
            'reason',
            'status',
            'employee_name',
            'employee_id',
            'passport_required_from',
            'passport_required_to',
            'address_during_leave',
            'ticket_eligibility',            
            'attachment_url',
            'signature_url',
            'approved_by_name',
            'rejection_reason',
        ]
        read_only_fields = fields
    
    def get_approved_by_name(self, obj):
        """Get the name of the approver"""
        if obj.approved_by:
            return obj.approved_by.employee_name if hasattr(obj.approved_by, 'employee_name') else str(obj.approved_by)
        return None
    
    def get_attachment_url(self, obj):
        """Get full URL for attachment"""
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
    
    def get_signature_url(self, obj):
        """Get full URL for signature"""
        if obj.signature:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.signature.url)
            return obj.signature.url
        return None
    


# ____________________
    
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['heading', 'status', 'address', 'task_assign_time', 'percentage_completed']



class BreakHistorySerializer(serializers.ModelSerializer):
    number_of_extended_breaks = serializers.IntegerField(source='number_of_scheduled_breaks')
    
    class Meta:
        model = BreakHistory
        fields = ['total_break_time', 'number_of_extended_breaks']



class HomeAPISerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='employee_name')  
    role = serializers.CharField(source='get_role_display')
    employee_type = serializers.CharField(source='get_employee_type_display')  
    notification_count = serializers.SerializerMethodField()
    ongoing_task = serializers.SerializerMethodField()
    ongoing_tasks = serializers.SerializerMethodField()
    break_timer = serializers.SerializerMethodField()
    break_history = serializers.SerializerMethodField()
    status_of_check = serializers.SerializerMethodField()
    check_in_out_time = serializers.SerializerMethodField()
    total_no_of_tasks_today = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    company_announcement_details = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'name',
            'role',
            'employee_type', 
            'notification_count',
            'ongoing_task',
            'ongoing_tasks', 
            'break_timer',
            'break_history',
            'status_of_check',
            'check_in_out_time',
            'total_no_of_tasks_today',
            'tasks',
            'company_announcement_details'
        ]

    def get_notification_count(self, obj):
        if hasattr(obj, 'notifications'):
            return obj.notifications.filter(is_read=False).count()
        return 0

    def get_ongoing_task(self, obj):
        """Returns True if there are any ongoing tasks, False otherwise"""
        ongoing_tasks = obj.tasks.filter(
            status__in=['paused', 'in_progress']
        )
        return ongoing_tasks.exists()

    def get_ongoing_tasks(self, obj):
        ongoing_tasks = obj.tasks.filter(
            status__in=['paused', 'in_progress']
        )
        return TaskSerializer(ongoing_tasks, many=True).data

    def get_break_timer(self, obj):
        today = timezone.now().date()
        current_break = obj.break_timers.filter(
            date=today,
            break_start_time__isnull=False
        ).last()
        return BreakTimerSerializer(current_break).data if current_break else None

    def get_break_history(self, obj):
        today = timezone.now().date()
        break_history = obj.break_histories.filter(date=today).first()
        return BreakHistorySerializer(break_history).data if break_history else None

    def get_status_of_check(self, obj):
        today = timezone.now().date()
        # Updated to use check_date field instead of check_time__date
        last_check = obj.attendance_checks.filter(
            check_date=today
        ).order_by('-created_at').first()  # Using created_at for ordering
        
        return last_check.check_type if last_check else "out"

    def get_check_in_out_time(self, obj):
        today = timezone.now().date()
        # Updated to use check_date field
        today_checks = obj.attendance_checks.filter(
            check_date=today
        ).order_by('created_at')  # Using created_at for ordering
        
        check_in = today_checks.filter(check_type='in').first()
        check_out = today_checks.filter(check_type='out').last()
        
        return {
            'check_in': {
                'time': check_in.check_time if check_in else None,
                'time_zone': check_in.time_zone if check_in else None,
                'location': check_in.location if check_in else None
            },
            'check_out': {
                'time': check_out.check_time if check_out else None,
                'time_zone': check_out.time_zone if check_out else None,
                'location': check_out.location if check_out else None,
                'reason': check_out.reason if check_out else None
            }
        }

    def get_total_no_of_tasks_today(self, obj):
        today = timezone.now().date()
        return obj.tasks.filter(task_assign_time__date=today).count()

    def get_tasks(self, obj):
        today = timezone.now().date()
        today_tasks = obj.tasks.filter(task_assign_time__date=today)
        
        tasks_data = []
        for task in today_tasks:
            task_data = {
                'type_of_task': task.task_type,
                'heading': task.heading,
                'address_or_sub_details': task.address,
                'time_of_task': task.task_assign_time
            }
            tasks_data.append(task_data)
        
        return tasks_data

    def get_company_announcement_details(self, obj):
        announcements = CompanyAnnouncement.objects.filter(
            is_active=True
        ).order_by('-date')[:3]
        return CompanyAnnouncementSerializer(announcements, many=True).data


    




