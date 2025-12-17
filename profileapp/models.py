from django.db import models
from authapp.models import Employee

# Create your models here.
class VisaDetails(models.Model):
    DOCUMENT_TYPES = [
        ('visa_copy', 'Visa Photo Copy'),
        ('labour_card', 'Labour Card Copy'),
        ('passport_copy', 'Passport Copy'),
        ('emirates_id', 'Emirates ID Copy'),
        ('work_permit', 'Work Permit Copy'),
    ]

    employee = models.OneToOneField(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='visa_details'
    )
    
    visa_expiry_date = models.DateField(blank=True, null=True)
    emirates_id_number = models.CharField(max_length=100, blank=True, null=True)
    emirates_id_expiry = models.DateField(blank=True, null=True)
    passport_number = models.CharField(max_length=100, blank=True, null=True)
    passport_expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    

    def __str__(self):
        return f"Visa Details - {self.employee.employeeId}"

    def get_pending_documents(self):
        """Get list of pending documents"""
        pending_docs = []
        document_fields = {
            'visa_copy': 'Visa Photo Copy',
            'labour_card': 'Labour Card Copy', 
            'passport_copy': 'Passport Copy',
            'emirates_id': 'Emirates ID Copy',
            'work_permit': 'Work Permit Copy',
        }
        
        for doc_type, doc_name in document_fields.items():
            if not self.documents.filter(document_type=doc_type).exists():
                pending_docs.append(doc_name)
                
        return pending_docs


class Document(models.Model):
    DOCUMENT_TYPES = [
        ('visa_copy', 'Visa Photo Copy'),
        ('labour_card', 'Labour Card Copy'),
        ('passport_copy', 'Passport Copy'),
        ('emirates_id', 'Emirates ID Copy'),
        ('work_permit', 'Work Permit Copy'),
    ]

    visa_details = models.ForeignKey(
        VisaDetails, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(
        upload_to='employee_documents/',
        max_length=255
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.visa_details.employee.employeeId}"
    


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('pickup', 'Pickup'),
        ('motorcycle', 'Motorcycle'),
    ]
    
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
        ('retired', 'Retired'),
    ]
    
    vehicle_number = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    registration_date = models.DateField()
    vehicle_expiry_date = models.DateField()
    insurance_expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vehicle_image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.vehicle_number} - {self.model}"


class VehicleAssignment(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='vehicle_assignment'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='assignments',
        null=True,
        blank=True
    )
    assigned_date = models.DateField()
    temporary_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='temporary_assignments',
        null=True,
        blank=True
    )
    temporary_vehicle_assigned_date = models.DateTimeField(null=True, blank=True)
    temporary_vehicle_ending_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.employee.employeeId} - {self.vehicle.vehicle_number if self.vehicle else 'No Vehicle'}"


class VehicleIssue(models.Model):
    ISSUE_STATUS = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='issues'
    )
    title = models.CharField(max_length=200)
    reported_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_vehicle_issues'
    )
    reported_date = models.DateField()
    status = models.CharField(max_length=20, choices=ISSUE_STATUS, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.title}"


class DailyOdometerReading(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='odometer_readings'
    )
    reading_date = models.DateField()
    start_km = models.DecimalField(max_digits=10, decimal_places=2)
    end_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-reading_date']
        unique_together = ['vehicle', 'reading_date']
    
    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.reading_date}: {self.start_km}km"