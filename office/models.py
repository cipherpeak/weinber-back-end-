from django.db import models

from authapp.models import Employee



class Note(models.Model):

    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Employee"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Title",
        help_text="Enter title for your note"
    )
    
    description = models.TextField(
        verbose_name="Note Description",
        help_text="Enter description for your note"
    )
    
    date = models.CharField(
        max_length=200,
        verbose_name="Date",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Note"
        verbose_name_plural = "Notes"
    
    def __str__(self):
        return f"{self.title} - {self.employee.employee_name}"