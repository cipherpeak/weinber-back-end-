# task/admin.py
from django.contrib import admin
from .models import Duty, Task, DeliveryTask, OfficeTask, ServiceTask, TaskDuty, TaskProgressImage,ServiceTaskDax


admin.site.register(Task)
admin.site.register(DeliveryTask)
admin.site.register(OfficeTask)
admin.site.register(ServiceTask)
admin.site.register(Duty)
admin.site.register(TaskDuty)
admin.site.register(TaskProgressImage)
admin.site.register(ServiceTaskDax)


