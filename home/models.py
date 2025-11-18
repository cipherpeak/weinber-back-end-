from datetime import timezone
from django.db import models
from authapp.models import Employee



class AttendanceCheck(models.Model):
    CHECK_TYPE_CHOICES = [
        ('in', 'Check In'),
        ('out', 'Check Out'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_checks')
    check_type = models.CharField(max_length=10, choices=CHECK_TYPE_CHOICES)
    check_date = models.DateField(blank=True,null=True)  
    check_time = models.CharField(max_length=100)
    time_zone = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.check_type} - {self.check_date}"
    
    def save(self, *args, **kwargs):
        # Auto-set check_date to today if not provided
        if not self.check_date:
            self.check_date = timezone.now().date()
        super().save(*args, **kwargs)
    

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




from django.utils import timezone

class CompanyAnnouncement(models.Model):
    heading = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Company Announcement'
        verbose_name_plural = 'Company Announcements'

    def __str__(self):
        return self.heading



