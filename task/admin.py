# task/admin.py
from django.contrib import admin
from .models import Task, DeliveryTask, OfficeTask, ServiceTask
from authapp.models import Employee  # Add this import

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'heading', 'task_type', 'status', 'task_time']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['heading', 'employee__employeeId']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "employee":
            kwargs["queryset"] = Employee.objects.all().order_by('employeeId')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Register other models...
admin.site.register(DeliveryTask)
admin.site.register(OfficeTask)
admin.site.register(ServiceTask)