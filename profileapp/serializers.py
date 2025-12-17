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
    reported_by_id = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleIssue
        fields = [
            'id', 'title', 
            'reported_by', 'reported_by_name', 'reported_by_id',
            'reported_date', 'status', 'created_at'
        ]
    
    def get_reported_by_name(self, obj):
        """Get reporter's full name"""
        if obj.reported_by:
            # Try different methods to get the name
            if hasattr(obj.reported_by, 'get_full_name'):
                full_name = obj.reported_by.get_full_name()
                if full_name:
                    return full_name
            
            if hasattr(obj.reported_by, 'first_name') and hasattr(obj.reported_by, 'last_name'):
                name = f"{obj.reported_by.first_name} {obj.reported_by.last_name}".strip()
                if name:
                    return name
            
            return str(obj.reported_by)
        return "Unknown"
    
    def get_reported_by_id(self, obj):
        """Get reporter's ID/employee ID"""
        if obj.reported_by:
            if hasattr(obj.reported_by, 'employeeId'):
                return obj.reported_by.employeeId
            elif hasattr(obj.reported_by, 'id'):
                return obj.reported_by.id
        return None


class DailyOdometerReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyOdometerReading
        fields = '__all__'
        read_only_fields = ['created_at']


class TemporaryVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_number', 'model', 'vehicle_type', 'fuel_type', 
                 'vehicle_expiry_date', 'insurance_expiry_date']


class VehicleDetailsSerializer(serializers.Serializer):
    class CurrentVehicleSerializer(serializers.Serializer):
        vehicle_image = serializers.SerializerMethodField()
        vehicle_number = serializers.CharField(source='vehicle.vehicle_number')
        model = serializers.CharField(source='vehicle.model')
        vehicle_type = serializers.CharField(source='vehicle.vehicle_type')
        assigned_date = serializers.DateField()
        reported_vehicle_issues = serializers.SerializerMethodField() 
        vehicle_expiry_date = serializers.DateField(source='vehicle.vehicle_expiry_date')
        insurance_expiry_date = serializers.DateField(source='vehicle.insurance_expiry_date')
        fuel_type = serializers.CharField(source='vehicle.fuel_type')
        odometer_start_km = serializers.SerializerMethodField()
        odometer_end_km = serializers.SerializerMethodField()




        def get_vehicle_image(self, obj):
            """Get vehicle image URL"""
            if obj.vehicle.vehicle_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.vehicle.vehicle_image.url)
                return obj.vehicle.vehicle_image.url
            return None        
        
        def get_reported_vehicle_issues(self, obj):
            """Get ALL reported issues for this vehicle"""
            issues = VehicleIssue.objects.filter(
                vehicle=obj.vehicle
            ).order_by('-reported_date', '-created_at')
            
            # Return serialized data with reporter details
            return VehicleIssueSerializer(issues, many=True).data
        
        def get_odometer_start_km(self, obj):
            try:
                from django.utils import timezone
                today = timezone.now().date()
                reading = DailyOdometerReading.objects.get(
                    vehicle=obj.vehicle,
                    reading_date=today
                )
                return reading.start_km
            except DailyOdometerReading.DoesNotExist:
                return None
        
        def get_odometer_end_km(self, obj):
            try:
                from django.utils import timezone
                today = timezone.now().date()
                reading = DailyOdometerReading.objects.get(
                    vehicle=obj.vehicle,
                    reading_date=today
                )
                return reading.end_km
            except DailyOdometerReading.DoesNotExist:
                return None
    
    current_vehicle = CurrentVehicleSerializer(source='*', allow_null=True)
    
    # FIX HERE: Remove source parameter when it's the same as field name
    temporary_vehicle_assigned_date = serializers.DateTimeField(allow_null=True)
    temporary_vehicle_ending_date = serializers.DateTimeField(allow_null=True)
    
    temporary_vehicle = serializers.SerializerMethodField()
    
    def get_temporary_vehicle(self, obj):
        if obj.temporary_vehicle:
            return TemporaryVehicleSerializer(obj.temporary_vehicle).data
        return None
    


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
