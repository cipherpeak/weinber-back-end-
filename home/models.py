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
        if not self.check_date:
            self.check_date = timezone.now().date()
        super().save(*args, **kwargs)
    

class BreakTimer(models.Model):
    BREAK_TYPE_CHOICES = [
        ('lunch', 'Lunch Break'),
        ('coffee', 'Coffee Break'),
        ('stretch', 'Stretch Break'),
        ('other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='break_timers')
    break_type = models.CharField(max_length=20, choices=BREAK_TYPE_CHOICES)
    custom_break_type = models.CharField(max_length=100, blank=True, null=True)  
    duration = models.CharField(max_length=20,default="10 min")  
    break_start_time = models.CharField(max_length=50) 
    break_end_time = models.CharField(max_length=50, blank=True, null=True) 
    date = models.DateField(auto_now_add=True) 
    reason = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    end_reason = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"{self.employee.employeeId} - {self.get_break_type_display()}"

    @property
    def display_break_type(self):
        """Return custom break type if break_type is 'other', otherwise the display name"""
        if self.break_type == '' and self.custom_break_type:
            return self.custom_break_type
        return self.get_break_type_display()
    

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





