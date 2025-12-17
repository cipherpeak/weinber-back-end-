from django.urls import path
from .views import *

urlpatterns = [
    path('', EmployeeProfileView.as_view(), name='employee-profile'),
    path('employee-information/', EmployeeInformationView.as_view(), name='employee-information'),
    path('personal-information/', EmployeePersonalInfoView.as_view(), name='personal-information'),
    path('personal-information/update/', EmployeePersonalInfoUpdateView.as_view(), name='personal-information-update'),
    path('visa-documents/', VisaDocumentsView.as_view(), name='visa-documents'),
    path('visa-documents/update/', VisaDocumentsUpdateView.as_view(), name='visa-documents-update'),
    path('vehicle-details/', VehicleDetailsAPIView.as_view(), name='vehicle-details'),
    path('vehicle-report/', ReportVehicleIssueAPIView.as_view(), name='vehicle-report'),
    path('create-temporary-vehicle/', CreateTemporaryVehicleAPIView.as_view(), name='create-temporary-vehicle'),


]
