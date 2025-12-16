from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Employee
from .serializers import EmployeeLoginSerializer, EmployeeSerializer

class EmployeeLoginView(APIView):
    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)
        if serializer.is_valid():
            employeeId = serializer.validated_data['employeeId']
            password = serializer.validated_data['password']

            try:
                employee = Employee.objects.get(employeeId=employeeId)
            except Employee.DoesNotExist:
                return Response({'error': 'Invalid Employee ID or Password'}, status=status.HTTP_401_UNAUTHORIZED)

            if employee.check_password(password):
                refresh = RefreshToken.for_user(employee)
                
                employee_serializer = EmployeeSerializer(employee, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'employee': employee_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid Employee ID or Password'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)