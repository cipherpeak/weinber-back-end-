from datetime import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Vehicle, VehicleAssignment, VehicleIssue, VisaDetails
from .serializers import CreateTemporaryVehicleSerializer, DocumentUpdateSerializer, EmployeeInformationSerializer, EmployeePersonalInfoSerializer, EmployeePersonalInfoUpdateSerializer, EmployeeProfileSerializer, ReportVehicleIssueSerializer, VehicleDetailsSerializer, VisaDetailsSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class EmployeeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user
            serializer = EmployeeProfileSerializer(
                employee,
                context={'request': request} 
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        


class EmployeeInformationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            employee = request.user
            serializer = EmployeeInformationSerializer(employee)

            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)    
        

        


class EmployeePersonalInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user
            serializer = EmployeePersonalInfoSerializer(employee)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)            
        


class EmployeePersonalInfoUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            employee = request.user
            serializer = EmployeePersonalInfoUpdateSerializer(
                employee, 
                data=request.data, 
                partial=True  
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Personal information updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)   



class VisaDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user
            
            visa_details, created = VisaDetails.objects.get_or_create(employee=employee)
            
            serializer = VisaDetailsSerializer(visa_details)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)     




class VisaDocumentsUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            employee = request.user
            
            # Get or create visa details for the employee
            visa_details, created = VisaDetails.objects.get_or_create(employee=employee)
            
            serializer = DocumentUpdateSerializer(
                data=request.data,
                context={'visa_details': visa_details}
            )
            
            if serializer.is_valid():
                updated_document = serializer.save()
                
                return Response({
                    "status": "success",
                    "message": "Document uploaded successfully",
                    "data": updated_document
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

from django.utils import timezone 
from .models import DailyOdometerReading

class VehicleDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:

            employee = request.user
            
            try:
                vehicle_assignment = VehicleAssignment.objects.get(employee=employee)
                
                if vehicle_assignment.vehicle:
                    
                    today = timezone.now().date()

                    # Create or get today's odometer reading
                    odometer_reading, created = DailyOdometerReading.objects.get_or_create(
                        vehicle=vehicle_assignment.vehicle,
                        reading_date=today,
                        defaults={'start_km': 0}  
                    )
                
                serializer = VehicleDetailsSerializer(
                    vehicle_assignment, 
                    context={'request': request}  
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            except VehicleAssignment.DoesNotExist:
                # If no vehicle is assigned
                return Response({
                    'current_vehicle': None,
                    'temporary_vehicle': None,
                    'message': 'No vehicle assigned'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



class ReportVehicleIssueAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):

        try:
            # Get current user
            user = request.user
            
            # Check if user has a vehicle assignment
            try:
                vehicle_assignment = VehicleAssignment.objects.get(employee=user)
                current_vehicle = vehicle_assignment.vehicle
                
                if not current_vehicle:
                    return Response(
                        {"error": "No vehicle assigned to this user"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate and save the issue
                serializer = ReportVehicleIssueSerializer(data=request.data)
                
                if serializer.is_valid():
                    # Create the issue with additional info
                    vehicle_issue = VehicleIssue.objects.create(
                        vehicle=current_vehicle,
                        title=serializer.validated_data['title'],
                        reported_date=serializer.validated_data['reported_date'],
                        status=serializer.validated_data['status'],
                        reported_by=user,
                    )
                    
                    # Return success response
                    return Response({
                        "message": "Vehicle issue reported successfully",
                        "issue_id": vehicle_issue.id,
                        "title": vehicle_issue.title,
                        "reported_date": vehicle_issue.reported_date,
                        "status": vehicle_issue.status,
                        "vehicle": current_vehicle.vehicle_number
                    }, status=status.HTTP_201_CREATED)
                
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            except VehicleAssignment.DoesNotExist:
                return Response(
                    {"error": "No vehicle assigned to this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Failed to report issue: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        




class CreateTemporaryVehicleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):

        try:

            serializer = CreateTemporaryVehicleSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            user = request.user
            
            vehicle= Vehicle.objects.get(
                vehicle_number=data['vehicle_number'].strip().upper(),
                defaults={
                    'model': data['vehicle_model'].strip(),
                    'vehicle_type': 'sedan',
                    'fuel_type': 'petrol',
                    'status': 'active'
                }
            )
            
            assignment = VehicleAssignment.objects.get(
                employee=user,
            )
            
            assignment.temporary_vehicle = vehicle
            assignment.temporary_vehicle_assigned_date = data['start_date']
            assignment.temporary_vehicle_assigned_time = data['start_time']
            assignment.temporary_vehicle_ending_date = data['end_date']
            assignment.temporary_vehicle_ending_time = data['end_time']
            assignment.note = data.get('add_note', '')
            assignment.location = data.get('location', '')
            assignment.save()
            
            return Response(
                {"success": True},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )