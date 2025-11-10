from rest_framework import serializers
from .models import ServiceTask, Task, TaskDuty, TaskProgressImage

class TaskListSerializer(serializers.ModelSerializer):
    task_id = serializers.IntegerField(source='id')
    title = serializers.CharField(source='heading')  
    iconType = serializers.CharField(source='icon_type') 

    class Meta:
        model = Task
        fields = ['task_id', 'title', 'description', 'due_date', 'iconType']
    

class TaskDetailSerializer(serializers.ModelSerializer):
    task_assigned = serializers.CharField(source='heading')
    scheduled_time = serializers.DateTimeField(source='task_assign_time')
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    service_tasks = serializers.SerializerMethodField()  # Add this field

    class Meta:
        model = Task
        fields = [
            'task_assigned',
            'customer_name', 
            'scheduled_time',
            'vehicle_model',
            'location',
            'task_notes',
            'priority_display',
            'service_tasks'  
        ]
    
    def get_task_type_display(self, obj):
        """Get task type display name"""
        if obj.task_type == 'service' and hasattr(obj, 'service_details'):
            return obj.service_details.get_service_type_display()
        return obj.get_task_type_display()
    

    def get_service_tasks(self, obj):
        """Get all service tasks for the same employee"""
        if obj.task_type == 'service':
            service_tasks = ServiceTask.objects.filter(
                task__employee=obj.employee
            ).select_related('task')
            
            service_tasks_data = []
            for service_task in service_tasks:
                service_tasks_data.append({
                    'service_type_display': service_task.get_service_type_display(),
                })
            return service_tasks_data
        return []
    

class TaskStatusSerializer(serializers.Serializer):
    title = serializers.CharField(source='heading')
    vehicle_details = serializers.SerializerMethodField()
    time_of_starting_task = serializers.DateTimeField(source='task_start_time')
    status_of_task = serializers.CharField(source='status')
    percentage_completed = serializers.IntegerField()

    def get_vehicle_details(self, obj):
        details = []
        if obj.vehicle_model:
            details.append(obj.vehicle_model)
        if obj.vehicle_year:
            details.append(str(obj.vehicle_year))
        if obj.vehicle_color:
            details.append(obj.vehicle_color)
        return ' - '.join(details) if details else (obj.vehicle_details or "")

class DutyListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='duty.name')
    description = serializers.CharField(source='duty.description')
    
    class Meta:
        model = TaskDuty
        fields = ['id', 'name', 'description', 'is_completed', 'completed_at']

class ProgressImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskProgressImage
        fields = ['image_url', 'percentage_completed', 'created_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class TaskDetailsResponseSerializer(serializers.Serializer):
    task_status = TaskStatusSerializer(source='*')
    duty_list = serializers.SerializerMethodField()
    progress_image = serializers.SerializerMethodField()

    def get_duty_list(self, obj):
        task_duties = obj.task_duties.select_related('duty').all()
        return DutyListSerializer(task_duties, many=True).data

    def get_progress_image(self, obj):
        latest_progress = obj.progress_images.order_by('-created_at').first()
        if latest_progress:
            return ProgressImageSerializer(latest_progress, context=self.context).data
        return None    
    


class SaveProgressSerializer(serializers.Serializer):
    progress_notes = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    duty_list = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    percentage = serializers.IntegerField(min_value=0, max_value=100, required=True)
    final_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)    



class PendingTaskSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='heading')
    vehicle_details = serializers.SerializerMethodField()
    task_assigned_date = serializers.DateTimeField(source='task_assign_time')
    percentage_completed = serializers.IntegerField()

    class Meta:
        model = Task
        fields = ['title', 'vehicle_details', 'task_assigned_date', 'percentage_completed']

    def get_vehicle_details(self, obj):
        details = []
        if obj.vehicle_model:
            details.append(obj.vehicle_model)
        if obj.vehicle_year:
            details.append(str(obj.vehicle_year))
        if obj.vehicle_color:
            details.append(obj.vehicle_color)
        return ' - '.join(details) if details else (obj.vehicle_details or "")

class PendingQueueSerializer(serializers.ModelSerializer):
    task_id = serializers.IntegerField(source='id')
    title = serializers.CharField(source='heading')
    vehicle_details = serializers.SerializerMethodField()
    due_date = serializers.DateTimeField()
    iconType = serializers.CharField(source='icon_type')

    class Meta:
        model = Task
        fields = ['task_id', 'title', 'vehicle_details', 'due_date', 'iconType']

    def get_vehicle_details(self, obj):
        details = []
        if obj.vehicle_model:
            details.append(obj.vehicle_model)
        if obj.vehicle_year:
            details.append(str(obj.vehicle_year))
        if obj.vehicle_color:
            details.append(obj.vehicle_color)
        return ' - '.join(details) if details else (obj.vehicle_details or "")