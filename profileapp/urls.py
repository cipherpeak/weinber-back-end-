from django.urls import path
from .views import *

urlpatterns = [
    path('', EmployeeProfileView.as_view(), name='employee-profile'),
    path('employee-information/', EmployeeInformationView.as_view(), name='employee-information'),
    path('personal-information/', EmployeePersonalInfoView.as_view(), name='personal-information'),
    path('personal-information/update/', EmployeePersonalInfoUpdateView.as_view(), name='personal-information-update'),
    path('visa-documents/', VisaDocumentsView.as_view(), name='visa-documents'),
    path('visa-documents/update/', VisaDocumentsUpdateView.as_view(), name='visa-documents-update'),

]
