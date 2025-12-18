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
from datetime import datetime

class VehicleDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            employee = request.user
            
            try:
                vehicle_assignment = VehicleAssignment.objects.get(employee=employee)
                

                if vehicle_assignment.status == 'temporary_vehicle':
                    try:
                        end_date_str = vehicle_assignment.temporary_vehicle_ending_date
                        end_time_str = vehicle_assignment.temporary_vehicle_ending_time
                        
                        if end_date_str and end_time_str:
                            end_datetime_str = f"{end_date_str} {end_time_str}"
                            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
                            
                            end_datetime = timezone.make_aware(end_datetime)
                            
                            now = timezone.now()
                            print(f"DEBUG: now={now}, end_datetime={end_datetime}")

                            if now >= end_datetime:
                                print("DEBUG: Temporary vehicle HAS expired")
                                vehicle_assignment.temporary_vehicle_number = None
                                vehicle_assignment.temporary_vehicle_model = None
                                vehicle_assignment.temporary_vehicle_type = None
                                vehicle_assignment.temporary_vehicle_fuel_type = None
                                vehicle_assignment.temporary_vehicle_insurance_expiry_date = None
                                vehicle_assignment.temporary_vehicle_assigned_date = None
                                vehicle_assignment.temporary_vehicle_assigned_time = None
                                vehicle_assignment.temporary_vehicle_ending_date = None
                                vehicle_assignment.temporary_vehicle_ending_time = None
                                vehicle_assignment.note = None
                                vehicle_assignment.location = None
                                
                                vehicle_assignment.status = 'current_vehicle'
                                
                                vehicle_assignment.save()
                                
                                print(f"DEBUG: Temporary vehicle expired for {employee.employeeId}. Status changed to 'current_vehicle'.")
                                
                    except (ValueError, TypeError) as e:
                        # Handle parsing errors gracefully
                        print(f"DEBUG: Error parsing temporary vehicle end datetime: {e}")
                        # You might want to handle this case differently
                

                if vehicle_assignment.vehicle and vehicle_assignment.status == 'current_vehicle':
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
            # Validate incoming data
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
            
            assignment, created = VehicleAssignment.objects.get_or_create(
                employee=user
            )
            
            assignment.temporary_vehicle_number = data['vehicle_number'].strip().upper()
            assignment.temporary_vehicle_model = data['vehicle_model'].strip()
            
            # Use a default or get from input if you add it to serializer
            assignment.temporary_vehicle_type = data['vehicle_type'] .strip()
            assignment.temporary_vehicle_fuel_type = data.get('fuel_type', 'petrol')
            
            # Dates and times (stored as CharField in your model)
            assignment.temporary_vehicle_assigned_date = data['start_date']
            assignment.temporary_vehicle_assigned_time = data['start_time']
            assignment.temporary_vehicle_ending_date = data['end_date']
            assignment.temporary_vehicle_ending_time = data['end_time']
            
            # Optional fields
            assignment.note = data.get('add_note', '')
            assignment.location = data.get('location', '')

            if 'vehicle_image' in request.FILES:
                assignment.temporary_vehicle_image = request.FILES['vehicle_image']

            # -- CRITICAL: Update the status to 'temporary_vehicle' --
            assignment.status = 'temporary_vehicle'
            
            # Save the updated assignment
            assignment.save()
            
            return Response(
                {"success": True, "message": "Temporary vehicle assigned successfully."},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # Log the exception here if needed
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )