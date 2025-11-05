from django.db import models
from authapp.models import Employee



class AttendanceCheck(models.Model):
    CHECK_TYPE_CHOICES = [
        ('in', 'Check In'),
        ('out', 'Check Out'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_checks')
    check_type = models.CharField(max_length=10, choices=CHECK_TYPE_CHOICES)
    check_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)  
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.check_type}"
    

class BreakTimer(models.Model):
    BREAK_TYPE_CHOICES = [
        ('scheduled', 'Scheduled Break'),
        ('unscheduled', 'Unscheduled Break'),
        ('lunch', 'Lunch Break'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='break_timers')
    break_type = models.CharField(max_length=20, choices=BREAK_TYPE_CHOICES)
    duration = models.DurationField(blank=True, null=True)  
    break_start_time = models.DateTimeField()
    break_end_time = models.DateTimeField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)  

    def __str__(self):
        return f"{self.employee.employeeId} - {self.break_type}"
    

class BreakHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='break_histories')
    total_break_time = models.DurationField()
    number_of_scheduled_breaks = models.IntegerField(default=0)
    date = models.DateField()
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.date}"


class CompanyAnnouncement(models.Model):
    heading = models.CharField(max_length=255)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.heading        




