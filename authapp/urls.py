from django.urls import path
from .views import EmployeeLoginView


urlpatterns = [
    path('login/', EmployeeLoginView.as_view(), name='employee-login'),
]
