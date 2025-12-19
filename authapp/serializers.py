from rest_framework import serializers
from .models import Employee,Company



class EmployeeLoginSerializer(serializers.Serializer):
    employeeId = serializers.CharField(
        required=True,  
        allow_blank=False, 
        max_length=50,  
        trim_whitespace=True  
    )
    password = serializers.CharField(
        write_only=True, 
        required=True,
        allow_blank=False,
        min_length=4
    )



class EmployeeSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    app_icon = serializers.SerializerMethodField()
    employee_type = serializers.CharField(source='get_employee_type_display')  

    class Meta:
        model = Employee
        fields = ['employeeId', 'employee_type', 'profile_pic', 'app_icon','role']
        read_only_fields = ['employeeId', 'employee_type', 'profile_pic', 'app_icon','role']
    
    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None
    
    def get_app_icon(self, obj):
        if obj.company and obj.company.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.company.logo.url)
            return obj.company.logo.url
        return None
    

