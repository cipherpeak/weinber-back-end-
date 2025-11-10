from rest_framework import serializers
from task.models import Task
from .models import *
from django.utils import timezone

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['heading', 'status', 'address', 'task_assign_time', 'percentage_completed']

class BreakTimerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakTimer
        fields = ['break_type', 'duration', 'break_start_time']

class BreakHistorySerializer(serializers.ModelSerializer):
    number_of_extended_breaks = serializers.IntegerField(source='number_of_scheduled_breaks')
    
    class Meta:
        model = BreakHistory
        fields = ['total_break_time', 'number_of_extended_breaks']

class CompanyAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAnnouncement
        fields = ['heading', 'body', 'date']

class HomeAPISerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='employee_name')  
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
        # Make sure you have a notifications relationship in your Employee model
        # If not, you'll need to add it or remove this field
        if hasattr(obj, 'notifications'):
            return obj.notifications.filter(is_read=False).count()
        return 0

    def get_ongoing_task(self, obj):
        """Returns True if there are any ongoing tasks, False otherwise"""
        today = timezone.now().date()
        ongoing_tasks = obj.tasks.filter(
            task_assign_time__date=today,
            status__in=['paused', 'in_progress']
        )
        return ongoing_tasks.exists()

    def get_ongoing_tasks(self, obj):
        today = timezone.now().date()
        ongoing_tasks = obj.tasks.filter(
            task_assign_time__date=today,
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
        last_check = obj.attendance_checks.filter(
            check_time__date=today
        ).order_by('-check_time').first()
        return last_check.check_type if last_check else "out"

    def get_check_in_out_time(self, obj):
        today = timezone.now().date()
        today_checks = obj.attendance_checks.filter(
            check_time__date=today
        ).order_by('check_time')
        
        check_in = today_checks.filter(check_type='in').first()
        check_out = today_checks.filter(check_type='out').last()
        
        return {
            'check_in': check_in.check_time if check_in else None,
            'check_out': check_out.check_time if check_out else None
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
    


class CheckInOutSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=255, required=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_location(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Location is required")
        return value

class BreakSerializer(serializers.Serializer):
    break_type = serializers.ChoiceField(
        choices=BreakTimer.BREAK_TYPE_CHOICES, 
        required=True
    )
    location = serializers.CharField(max_length=255, required=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_break_type(self, value):
        if value not in dict(BreakTimer.BREAK_TYPE_CHOICES):
            raise serializers.ValidationError("Invalid break type")
        return value    