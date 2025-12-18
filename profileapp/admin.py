from django.contrib import admin

from .models import Document, VisaDetails,Vehicle,VehicleAssignment,VehicleIssue,DailyOdometerReading,TemporaryVehicleHistory

# Register your models here.
admin.site.register(VisaDetails)
admin.site.register(Document)
admin.site.register(Vehicle)
admin.site.register(VehicleAssignment)
admin.site.register(VehicleIssue)
admin.site.register(DailyOdometerReading)
admin.site.register(TemporaryVehicleHistory)



