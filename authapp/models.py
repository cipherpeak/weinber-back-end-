from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class EmployeeManager(BaseUserManager):
    def create_user(self, employeeId, password=None, **extra_fields):
        if not employeeId:
            raise ValueError("The Employee ID must be set")

        extra_fields.setdefault("is_active", True)

        user = self.model(employeeId=employeeId, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employeeId, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "super_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(employeeId, password, **extra_fields)


class Company(models.Model):
    COMPANY_CHOICES = [
        ("dax", "DAX"),
        ("advantage", "Advantage"),
        ("milan", "Milan"),
        ("redronic", "Redronic"),
    ]

    company_name = models.CharField(
        max_length=100, choices=COMPANY_CHOICES, blank=True, null=True
    )
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(
        upload_to="company_logos/", blank=True, null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name or "Company"


class Employee(AbstractBaseUser, PermissionsMixin):

    EMPLOYEE_TYPE_CHOICES = [
        ("service", "Service"),
        ("deliver", "Deliver"),
        ("office", "Office"),
        ("mechanic", "Mechanic"),
    ]

    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("admin", "Admin"),
        ("employee", "Employee"),
    ]

    employeeId = models.CharField(max_length=50, unique=True)
    employee_name = models.CharField(max_length=100, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="employees",
    )

    employee_type = models.CharField(
        max_length=20, choices=EMPLOYEE_TYPE_CHOICES, default="service"
    )

    profile_pic = models.ImageField(
        upload_to="employee_profile_pics/", blank=True, null=True
    )

    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="employee"
    )
    
    home_address = models.TextField(blank=True, null=True)

    nationality = models.CharField(max_length=20, blank=True, null=True)

    date_of_birth = models.DateField(auto_now_add=True,blank=True, null=True)

    emergency_contact_name = models.CharField(max_length=20, blank=True, null=True)

    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)

    emergency_contact_relation = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Can log into admin panel",
    )

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = EmployeeManager()

    USERNAME_FIELD = "employeeId"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["employeeId"]

    def __str__(self):
        return self.employeeId
