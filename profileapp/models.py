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
    
    visa_number = models.CharField(max_length=100, blank=True, null=True)
    visa_expiry_date = models.DateField(blank=True, null=True)
    
    passport_number = models.CharField(max_length=100, blank=True, null=True)
    passport_expiry_date = models.DateField(blank=True, null=True)
    
    emirates_id_expiry = models.DateField(blank=True, null=True)
    
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