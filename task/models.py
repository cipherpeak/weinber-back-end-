from django.db import models
from authapp.models import Employee


class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('paused', 'Paused'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('on_hold', 'On Hold'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('nothing', 'Nothing Task'),
        ('delivery', 'Delivery'),
        ('office', 'Office'),
        ('service', 'Service/Detailing'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    ICON_TYPE_CHOICES = [
        ('nothing', 'Nothing'),
        ('ongoing', 'Ongoing'),
        ('delivery', 'Delivery'),
        ('office', 'Office'),
        ('service', 'Service'),
        ('mechanic', 'Mechanic'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    heading = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='not_started')
    address = models.TextField(blank=True, null=True)
    task_assign_time = models.DateTimeField(blank=True, null=True)
    task_start_time = models.DateTimeField(blank=True, null=True)
    task_completed_date = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    vehicle_details = models.TextField(blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True) 
    vehicle_year = models.IntegerField(blank=True, null=True) 
    vehicle_color = models.CharField(max_length=50, blank=True, null=True) 
    vehicle_image_before = models.ImageField(upload_to='vehicle_images/before/', blank=True, null=True)
    vehicle_image_after = models.ImageField(upload_to='vehicle_images/after/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)  
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    task_notes = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    location = models.CharField(max_length=500, blank=True, null=True)
    icon_type = models.CharField(max_length=20, choices=ICON_TYPE_CHOICES, default='nothing') 
    percentage_completed = models.IntegerField(default=0)
    is_nothing_task = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.heading}"
       
    def save(self, *args, **kwargs):
        if not self.icon_type or self.icon_type == 'nothing':
            self.icon_type = self.task_type
        super().save(*args, **kwargs)
    
class DeliveryTask(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='delivery_details')
    invoice_numbers = models.TextField()
    delivery_location = models.TextField()
    
    def __str__(self):
        return f"Delivery - {self.task.heading}"


class OfficeTask(models.Model):
    OFFICE_TASK_TYPE_CHOICES = [
        ('employee_verification', 'Employee Verification'),
        ('task_verification', 'Task Verification'),
        ('record_work', 'Record Daily Work'),
        ('send_reminders', 'Send Reminders'),
        ('view_profiles', 'View Employee Profiles'),
    ]
    
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='office_details')
    office_task_type = models.CharField(max_length=50, choices=OFFICE_TASK_TYPE_CHOICES)
    specific_date = models.DateField(blank=True, null=True)
    employee_profiles_to_review = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Office - {self.office_task_type}"


class ServiceTask(models.Model):

    SERVICE_TYPE_CHOICES = [
        ('car_wash', 'Car Wash'),
        ('full_service', 'Full Service'),
        ('paint_protection_film_wrapping', 'Paint Protection - Film Wrapping'),
        ('window_tinting', 'Window - Tinting'),
        ('advanced_borophene_coating', 'Advanced Borophene - Coating'),
        ('premium_graphene_coating', 'Premium Graphene - Coating'),
        ('premium_nanoceramic_coating', 'Premium Nanoceramic - Coating'),
        ('exterior_detailing', 'Exterior - Detailing'),
        ('interior_detailing', 'Interior - Detailing'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='service_tasks')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    time_taken = models.DurationField(blank=True, null=True)
    vin_number = models.CharField(max_length=100)
    vin_image = models.ImageField(upload_to='vin_images/', blank=True, null=True)
    shared_staff_details = models.TextField(blank=True, null=True)
    work_location = models.CharField(max_length=255)
    work_start_time = models.DateTimeField(blank=True, null=True)
    work_end_time = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Service - {self.service_type}"
    


class Duty(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class TaskDuty(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_duties')
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.task.heading} - {self.duty.name}"

class TaskProgressImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='progress_images')
    image = models.ImageField(upload_to='task_progress_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.task.heading} - {self.percentage_completed}%"    
