from datetime import timezone
from django.db import models
from authapp.models import Employee
from django.core.validators import MinValueValidator
from django.utils import timezone



class AttendanceCheck(models.Model):
    CHECK_TYPE_CHOICES = [
        ('in', 'Check In'),
        ('out', 'Check Out'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_checks')
    check_type = models.CharField(max_length=10, choices=CHECK_TYPE_CHOICES)
    check_date = models.CharField(max_length=100)  
    check_time = models.CharField(max_length=100)
    time_zone = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.check_type} - {self.check_date}"

    

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
    duration = models.CharField(max_length=20,null=True,blank=True)  
    break_start_time = models.CharField(max_length=50) 
    break_end_time = models.CharField(max_length=50, blank=True, null=True) 
    date = models.CharField(max_length=100, blank=True, null=True)  
    location = models.CharField(max_length=255, blank=True, null=True)
    end_reason = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"{self.employee.employeeId} - {self.get_break_type_display()}"

    @property
    def display_break_type(self):
        if self.break_type == 'other' and self.custom_break_type:
            return self.custom_break_type
        return self.get_break_type_display()
    

class BreakHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='break_histories')
    total_break_time = models.DurationField()
    number_of_scheduled_breaks = models.IntegerField(default=0)
    date = models.DateField()
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.date}"





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





class Leave(models.Model):

    LEAVE_CATEGORY_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('emergency', 'Emergency Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    TICKET_ELIGIBILITY_CHOICES = [
        ('eligible', 'Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('partial', 'Partial'),
    ]
    

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves'
    )

    # Basic leave information
    category = models.CharField(
        max_length=20,
        choices=LEAVE_CATEGORY_CHOICES,
        verbose_name="Category of Leave"
    )
    
    start_date = models.CharField(max_length=100)  
    
    end_date = models.CharField(max_length=100)  
    
    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(0.5)],
        verbose_name="Total Number of Leave Days"
    )
    
    reason = models.TextField(
        verbose_name="Reason for the Leave",
        blank=True,
        null=True
    )
    
    passport_required_from = models.CharField(max_length=100,null=True,blank=True)  
    
    passport_required_to = models.CharField(max_length=100,null=True,blank=True)  
    
    address_during_leave = models.TextField(
        blank=True,
        null=True,
        verbose_name="Address During the Leave"
    )
    
    ticket_eligibility = models.CharField(
        max_length=100,
        choices=TICKET_ELIGIBILITY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Ticket Eligibility"
    )
    

    # Attachments
    attachment = models.FileField(
        upload_to='leave_attachments/',
        blank=True,
        null=True,
        verbose_name="Attach Media"
    )

    signature = models.FileField(
        upload_to='signature_attachments/',
        blank=True,
        null=True,
        verbose_name="Attach Media"
    )

    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_leaves'
    )
    
    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )
    
    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Leave Application"
        verbose_name_plural = "Leave Applications"
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.category} ({self.start_date} to {self.end_date})"
    







