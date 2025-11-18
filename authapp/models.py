from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class EmployeeManager(BaseUserManager):
    def create_user(self, employeeId, password=None, **extra_fields):
        if not employeeId:
            raise ValueError('The Employee ID must be set')
        user = self.model(employeeId=employeeId, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employeeId, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(employeeId, password, **extra_fields)

class Employee(AbstractBaseUser, PermissionsMixin):
    EMPLOYEE_TYPE_CHOICES = [
        ('service', 'Service'),
        ('deliver', 'Deliver'),
        ('office', 'Office'),
        ('mechanic', 'Mechanic'),
    ]

    DESIGNATION_CHOICES = [
        ('car_service_associate', 'Car Service Associate'),
        ('service_advisor', 'Service Advisor'),
        ('service_supervisor', 'Service Supervisor'),
        ('service_manager', 'Service Manager'),
    ]

    DEPARTMENT_CHOICES = [
        ('service', 'Service Department'),
        ('delivery', 'Delivery Department'),
        ('office', 'Office Administration'),
        ('mechanic', 'Mechanic Department'),
        ('quality', 'Quality Control'),
        ('customer_service', 'Customer Service'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('it', 'IT Support'),
    ]

    RELATION_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('spouse', 'Spouse'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]
    
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]

    employeeId = models.CharField(max_length=50, unique=True)
    employee_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )
    
    profile_pic = models.ImageField(
        upload_to='employee_profile_pics/',
        blank=True, 
        null=True,
        max_length=255
    )
    
    app_icon = models.ImageField(
        upload_to='app_icons/',
        blank=True, 
        null=True,
        max_length=255
    )

    employee_type = models.CharField(
        max_length=20, 
        choices=EMPLOYEE_TYPE_CHOICES,
        default='service'
    )

    designation = models.CharField(
        max_length=30,
        choices=DESIGNATION_CHOICES,
        default='car_service_associate'
    )

    department = models.CharField(
        max_length=30,
        choices=DEPARTMENT_CHOICES,
        default='service'
    )

    branch_location = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    company_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='Your Company Name'
    )
    
    date_of_joining = models.DateField(
        blank=True,
        null=True
    )
    
    reporting_manager = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # New Personal Information fields
    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    
    email = models.EmailField(
        blank=True,
        null=True
    )
    
    home_address = models.TextField(
        blank=True,
        null=True
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True
    )
    
    nationality = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    
    # Emergency Contact Information
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    emergency_contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    
    emergency_contact_relation = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        blank=True,
        null=True
    )

    objects = EmployeeManager()

    USERNAME_FIELD = 'employeeId'
    REQUIRED_FIELDS = []  

    def __str__(self):
        return self.employeeId

    def get_profile_pic_base64(self):
        if self.profile_pic:
            import base64
            try:
                with open(self.profile_pic.path, 'rb') as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            except:
                return None
        return None

    # These methods are required by Django admin
    def get_full_name(self):
        return self.employeeId

    def get_short_name(self):
        return self.employeeId

    # Role-based methods
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_employee(self):
        return self.role == 'employee'