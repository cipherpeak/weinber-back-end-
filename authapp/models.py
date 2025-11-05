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

    employeeId = models.CharField(max_length=50, unique=True)
    employee_name = models.CharField(max_length=100, blank=True, null=True)
    # Required fields for custom user model
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
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