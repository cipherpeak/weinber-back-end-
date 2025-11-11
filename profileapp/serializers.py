from rest_framework import serializers
from authapp.models import Employee
from .models import Document, VisaDetails

class EmployeeProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'employeeId',
            'employee_name', 
            'profile_pic',
            'employee_type',
            'designation'
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
    
    class Meta:
        model = Employee
        fields = [
            'full_name',
            'employee_id', 
            'department',
            'branch_location',
            'company_name',
            'date_of_joining',
            'reporting_manager'
        ]        


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
            'visa_number',
            'visa_expiry_date',
            'passport_number', 
            'passport_expiry_date',
            'emirates_id_expiry',
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