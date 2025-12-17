from datetime import timezone
from rest_framework import serializers
from authapp.models import Employee
from .models import Document, VehicleIssue, VisaDetails, Vehicle, DailyOdometerReading

class EmployeeProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    employee_type = serializers.CharField(source='get_employee_type_display')  

    class Meta:
        model = Employee
        fields = [
            'employeeId',
            'employee_name', 
            'profile_pic',
            'employee_type',
        ]

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None

    


class EmployeeInformationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='employee_name')
    employee_id = serializers.CharField(source='employeeId')
    employee_type = serializers.CharField(source='get_employee_type_display')  
    company_name = serializers.SerializerMethodField()
    company_location = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'full_name',
            'employee_id', 
            'employee_type',
            'company_name',
            'date_joined',
            'company_location',
        ]   

    def get_company_name(self, obj):
        if obj.company and obj.company.company_name:
            return obj.company.company_name
        return None  
    
    def get_company_location(self, obj):
        if obj.company and obj.company.address:
            return obj.company.address
        return None     


class EmployeePersonalInfoSerializer(serializers.ModelSerializer):
    pro_pic = serializers.SerializerMethodField()
    mob_number = serializers.CharField(source='mobile_number')
    employee_home_address = serializers.CharField(source='home_address')
    dob = serializers.DateField(source='date_of_birth')
    emergency_contact_info = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'pro_pic',
            'mob_number',
            'email',
            'employee_home_address',
            'dob',
            'nationality',
            'emergency_contact_info'
        ]

    def get_pro_pic(self, obj):
        if obj.profile_pic:  
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)  
            return obj.profile_pic.url  
        return None

    def get_emergency_contact_info(self, obj):
        """Return emergency contact information as list"""
        if obj.emergency_contact_name and obj.emergency_contact_number:
            return [{
                'emergency_contacts_full_name': obj.emergency_contact_name,
                'mob_number': obj.emergency_contact_number,
                'relation_with_employee': obj.emergency_contact_relation
            }]
        return []       



class EmployeePersonalInfoUpdateSerializer(serializers.ModelSerializer):
    mob_number = serializers.CharField(source='mobile_number', required=False, allow_blank=True)
    employee_address = serializers.CharField(source='home_address', required=False, allow_blank=True)
    emergency_contact_info = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )
    
    emergency_contact_info_response = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'mob_number',
            'email',
            'employee_address',
            'emergency_contact_info',
            'emergency_contact_info_response'
        ]

    def update(self, instance, validated_data):
        emergency_contact_info = validated_data.pop('emergency_contact_info', None)
        
        instance = super().update(instance, validated_data)
        
        if emergency_contact_info and len(emergency_contact_info) > 0:
            contact_data = emergency_contact_info[0]  
            instance.emergency_contact_name = contact_data.get('emergency_contacts_full_name', instance.emergency_contact_name)
            instance.emergency_contact_number = contact_data.get('mob_number', instance.emergency_contact_number)
            instance.emergency_contact_relation = contact_data.get('relation_with_employee', instance.emergency_contact_relation)
            instance.save()
        
        return instance

    def get_emergency_contact_info_response(self, obj):
        """Return emergency contact information as list in response"""
        if obj.emergency_contact_name and obj.emergency_contact_number:
            return [{
                'emergency_contacts_full_name': obj.emergency_contact_name,
                'mob_number': obj.emergency_contact_number,
                'relation_with_employee': obj.emergency_contact_relation
            }]
        return []
    

class DocumentSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = Document
        fields = ['document_type', 'document_name', 'document_file', 'uploaded_at']


class VisaDetailsSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    pending_documents_list = serializers.SerializerMethodField()

    class Meta:
        model = VisaDetails
        fields = [
            'visa_expiry_date',
            'emirates_id_number',
            'emirates_id_expiry',
            'passport_number', 
            'passport_expiry_date',
            'documents',
            'pending_documents_list'
        ]

    def get_pending_documents_list(self, obj):
        """Get list of pending document names"""
        return obj.get_pending_documents()


class DocumentUpdateSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(
        choices=[
            ('visa_copy', 'Visa Photo Copy'),
            ('labour_card', 'Labour Card Copy'),
            ('passport_copy', 'Passport Copy'),
            ('emirates_id', 'Emirates ID Copy'),
            ('work_permit', 'Work Permit Copy'),
        ],
        required=True
    )
    document_file = serializers.FileField(required=True)

    def save(self, **kwargs):
        visa_details = self.context['visa_details']
        document_type = self.validated_data['document_type']
        document_file = self.validated_data['document_file']
        
        # Delete existing document of same type if exists
        Document.objects.filter(
            visa_details=visa_details, 
            document_type=document_type
        ).delete()
        
        # Create new document
        document = Document.objects.create(
            visa_details=visa_details,
            document_type=document_type,
            document_file=document_file
        )
        
        return {
            'document_type': document.document_type,
            'document_name': document.get_document_type_display(),
            'document_file': document.document_file.url if document.document_file else None
        }



class VehicleSerializer(serializers.ModelSerializer):
    vehicle_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_vehicle_image_url(self, obj):
        if obj.vehicle_image and hasattr(obj.vehicle_image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.vehicle_image.url)
            return obj.vehicle_image.url
        return None        


class VehicleIssueSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()

    class Meta:
        model = VehicleIssue
        fields = [
            'id', 'title', 
            'reported_by_name',
            'reported_date', 'status'
        ]

    def get_reported_by_name(self, obj):
        """Get reporter's full name"""
        if obj.reported_by:
            # Try different methods to get the name
            if obj.reported_by.employee_name:
                full_name = obj.reported_by.employee_name
                if full_name:
                    return full_name
            return str(obj.reported_by)
        return "Unknown"
    


class DailyOdometerReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyOdometerReading
        fields = '__all__'
        read_only_fields = ['created_at']




class VehicleDetailsSerializer(serializers.Serializer):
    class CurrentVehicleSerializer(serializers.Serializer):
        vehicle_image = serializers.SerializerMethodField()
        vehicle_number = serializers.SerializerMethodField()
        model = serializers.SerializerMethodField()
        vehicle_type = serializers.SerializerMethodField()
        assigned_date = serializers.SerializerMethodField()
        ending_date = serializers.SerializerMethodField()
        insurance_expiry_date = serializers.SerializerMethodField()
        fuel_type = serializers.SerializerMethodField()
        odometer_start_km = serializers.SerializerMethodField()
        odometer_end_km = serializers.SerializerMethodField()
        reported_vehicle_issues = serializers.SerializerMethodField() 

        def get_vehicle_image(self, obj):
            """Get vehicle image URL"""
            if obj.vehicle and obj.vehicle.vehicle_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.vehicle.vehicle_image.url)
                return obj.vehicle.vehicle_image.url
            return None        
        
        def get_vehicle_number(self, obj):
            """Get vehicle number"""
            if obj.vehicle:
                return obj.vehicle.vehicle_number
            return None
        
        def get_model(self, obj):
            """Get vehicle model"""
            if obj.vehicle:
                return obj.vehicle.model
            return None
        
        def get_vehicle_type(self, obj):
            """Get vehicle type"""
            if obj.vehicle:
                return obj.vehicle.vehicle_type
            return None
        
        def get_assigned_date(self, obj):
            return obj.current_vehicle_assigned_date
        
        def get_ending_date(self, obj):
            return obj.current_vehicle_ending_date
        
        def get_insurance_expiry_date(self, obj):
            if obj.vehicle:
                return obj.vehicle.insurance_expiry_date
            return None
        
        def get_fuel_type(self, obj):
            if obj.vehicle:
                return obj.vehicle.get_fuel_type_display()
            return None
        
        def get_reported_vehicle_issues(self, obj):
            """Get ALL reported issues for this vehicle"""
            if obj.vehicle:
                issues = VehicleIssue.objects.filter(
                    vehicle=obj.vehicle
                ).order_by('-reported_date', '-created_at')
                
                return VehicleIssueSerializer(issues, many=True).data
            return []
        
        def get_odometer_start_km(self, obj):
            try:
                from django.utils import timezone
                today = timezone.now().date()
                if obj.vehicle:
                    reading = DailyOdometerReading.objects.get(
                        vehicle=obj.vehicle,
                        reading_date=today
                    )
                    return reading.start_km
            except DailyOdometerReading.DoesNotExist:
                return None
            return None
        
        def get_odometer_end_km(self, obj):
            try:
                from django.utils import timezone
                today = timezone.now().date()
                if obj.vehicle:
                    reading = DailyOdometerReading.objects.get(
                        vehicle=obj.vehicle,
                        reading_date=today
                    )
                    return reading.end_km
            except DailyOdometerReading.DoesNotExist:
                return None
            return None
    
    class TemporaryVehicleSerializer(serializers.Serializer):
        vehicle_image = serializers.SerializerMethodField()
        vehicle_number = serializers.SerializerMethodField()
        model = serializers.SerializerMethodField()
        vehicle_type = serializers.SerializerMethodField()
        temporary_vehicle_assigned_date = serializers.SerializerMethodField()
        temporary_vehicle_ending_date = serializers.SerializerMethodField()
        insurance_expiry_date = serializers.SerializerMethodField()
        fuel_type = serializers.SerializerMethodField()
        odometer_start_km = serializers.SerializerMethodField()
        odometer_end_km = serializers.SerializerMethodField()
        reported_vehicle_issues = serializers.SerializerMethodField()
        
        def get_vehicle_image(self, obj):
            """Get vehicle image URL"""
            # Temporary vehicle doesn't have image in your model
            # If you want to store temp vehicle images, you need to add a field
            return None
        
        def get_vehicle_number(self, obj):
            """Get temporary vehicle number"""
            return obj.temporary_vehicle_number
        
        def get_model(self, obj):
            """Get temporary vehicle model"""
            return obj.temporary_vehicle_model
        
        def get_vehicle_type(self, obj):
            """Get temporary vehicle type"""
            return obj.temporary_vehicle_type
        
        def get_temporary_vehicle_assigned_date(self, obj):
            """Get assigned date for temporary vehicle"""
            return obj.temporary_vehicle_assigned_date
        
        def get_temporary_vehicle_ending_date(self, obj):
            """Get ending date for temporary vehicle"""
            return obj.temporary_vehicle_ending_date
        
        def get_insurance_expiry_date(self, obj):
            """Get insurance expiry date for temporary vehicle"""
            return obj.temporary_vehicle_insurance_expiry_date
        
        def get_fuel_type(self, obj):
            """Get fuel type for temporary vehicle"""
            return obj.temporary_vehicle_fuel_type
        
        def get_reported_vehicle_issues(self, obj):
            """Get reported issues for temporary vehicle"""
            # Temporary vehicles in your model don't have a Vehicle relation
            # So we can't get issues from VehicleIssue model
            # Return empty list or you need to change your model structure
            return []
        
        def get_odometer_start_km(self, obj):
            """Get odometer start km for temporary vehicle"""
            # Temporary vehicles don't have odometer readings in your current model
            # You would need to store this separately or add to VehicleAssignment
            return None
        
        def get_odometer_end_km(self, obj):
            """Get odometer end km for temporary vehicle"""
            # Temporary vehicles don't have odometer readings in your current model
            return None
    
    current_vehicle = CurrentVehicleSerializer(source='*', allow_null=True)
    temporary_vehicle = TemporaryVehicleSerializer(source='*', allow_null=True)

    


class ReportVehicleIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleIssue
        fields = ['title', 'reported_date', 'status']
        extra_kwargs = {
            'title': {'required': True},
            'reported_date': {'required': True},
            'status': {'required': True},
        }
    
    def validate_status(self, value):
        """Validate status choices"""
        valid_statuses = ['open', 'in_progress', 'resolved', 'ignored']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return value
    
    def validate_reported_date(self, value):
        """Validate reported date is not in the future"""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Reported date cannot be in the future")
        return value
    

from django.utils import timezone
from datetime import datetime
import re

class CreateTemporaryVehicleSerializer(serializers.Serializer):
    vehicle_number = serializers.CharField(
        max_length=50, 
        required=True,
        trim_whitespace=True,
        help_text="Vehicle registration number"
    )
    vehicle_model = serializers.CharField(
        max_length=100, 
        required=True,
        trim_whitespace=True,
        help_text="Vehicle model name"
    )
    start_date = serializers.CharField(
        max_length=100, 
        required=True,
        help_text="Start date (YYYY-MM-DD format)"
    )
    end_date = serializers.CharField(
        max_length=100, 
        required=True,
        help_text="End date (YYYY-MM-DD format)"
    )
    start_time = serializers.CharField(
        max_length=100, 
        required=True,
        help_text="Start time (HH:MM format, 24-hour)"
    )
    end_time = serializers.CharField(
        max_length=100, 
        required=True,
        help_text="End time (HH:MM format, 24-hour)"
    )
    add_note = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=1000,
        help_text="Additional notes about the assignment"
    )
    location = serializers.CharField(
        max_length=255, 
        required=False, 
        allow_blank=True,
        help_text="Location where vehicle will be used"
    )
    
    def validate_vehicle_number(self, value):
        """Validate vehicle number format"""
        value = value.strip().upper()
        
        if not value:
            raise serializers.ValidationError("Vehicle number cannot be empty")
        
        if len(value) < 3:
            raise serializers.ValidationError("Vehicle number is too short")
        
        return value
    
    def validate_vehicle_model(self, value):
        """Validate vehicle model"""
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError("Vehicle model cannot be empty")
        
        if len(value) < 2:
            raise serializers.ValidationError("Vehicle model is too short")
        
        return value
    
    def validate_start_date(self, value):
        """Validate start date format and logic"""
        value = value.strip()
        
        # Check if it's a valid date format (YYYY-MM-DD)
        try:
            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise serializers.ValidationError(
                "Start date must be in YYYY-MM-DD format (e.g., 2024-12-18)"
            )
        
        # Check if date is not in the past
        today = timezone.now().date()
        if parsed_date < today:
            raise serializers.ValidationError("Start date cannot be in the past")
        
        return value
    
    def validate_end_date(self, value):
        """Validate end date format"""
        value = value.strip()
        
        try:
            parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise serializers.ValidationError(
                "End date must be in YYYY-MM-DD format (e.g., 2024-12-20)"
            )
        
        return value
    
    def validate_start_time(self, value):
        """Validate start time format (24-hour format)"""
        value = value.strip()
        
        # Check HH:MM format (24-hour)
        time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
        if not re.match(time_pattern, value):
            raise serializers.ValidationError(
                "Start time must be in HH:MM format (24-hour, e.g., 09:00 or 14:30)"
            )
        
        return value
    
    def validate_end_time(self, value):
        """Validate end time format"""
        value = value.strip()
        
        time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
        if not re.match(time_pattern, value):
            raise serializers.ValidationError(
                "End time must be in HH:MM format (24-hour, e.g., 18:00 or 21:45)"
            )
        
        return value    




