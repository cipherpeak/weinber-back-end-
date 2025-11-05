from rest_framework import serializers
from .models import Employee

class EmployeeLoginSerializer(serializers.Serializer):
    employeeId = serializers.CharField()
    password = serializers.CharField(write_only=True)

class EmployeeSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    app_icon = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['employeeId', 'employee_type', 'profile_pic', 'app_icon']
        read_only_fields = ['employeeId', 'employee_type', 'profile_pic', 'app_icon']
    
    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None
    
    def get_app_icon(self, obj):
        if obj.app_icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.app_icon.url)
            return obj.app_icon.url
        return None  