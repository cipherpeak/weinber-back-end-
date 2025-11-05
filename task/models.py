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
        ('ongoing', 'Ongoing Task'),
        ('delivery', 'Delivery'),
        ('office', 'Office'),
        ('service', 'Service/Detailing'),
        ('mechanic', 'Mechanic'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    heading = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='not_started')
    address = models.TextField(blank=True, null=True)
    task_time = models.DateTimeField()
    percentage_completed = models.IntegerField(default=0)
    is_nothing_task = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.heading}"
   
    
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
        ('detailing_interior', 'Detailing - Interior'),
        ('car_wash', 'Car Wash'),
        ('full_service', 'Full Service'),
    ]
    
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='service_details')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    time_taken = models.DurationField()
    vehicle_details = models.TextField()
    vin_number = models.CharField(max_length=100)
    vin_image = models.ImageField(upload_to='vin_images/', blank=True, null=True)
    vehicle_image_before = models.ImageField(upload_to='vehicle_images/before/', blank=True, null=True)
    vehicle_image_after = models.ImageField(upload_to='vehicle_images/after/', blank=True, null=True)
    shared_staff_details = models.TextField(blank=True, null=True)
    work_location = models.CharField(max_length=255)
    work_start_time = models.DateTimeField()
    work_end_time = models.DateTimeField()
    
    def __str__(self):
        return f"Service - {self.service_type}"
