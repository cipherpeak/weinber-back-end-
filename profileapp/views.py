from datetime import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from home.models import AttendanceCheck
from .models import TemporaryVehicleHistory, Vehicle, VehicleAssignment, VehicleIssue, VisaDetails
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
import pytz

class VehicleDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            employee = request.user
            
            try:
                vehicle_assignment = VehicleAssignment.objects.get(employee=employee)
                
                # Get Dubai timezone
                dubai_tz = pytz.timezone('Asia/Dubai')
                
                if vehicle_assignment.status == 'temporary_vehicle':
                    try:
                        end_date_str = vehicle_assignment.temporary_vehicle_ending_date
                        end_time_str = vehicle_assignment.temporary_vehicle_ending_time
                        
                        if end_date_str and end_time_str:
                            end_datetime_str = f"{end_date_str} {end_time_str}"
                            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
                            end_datetime = timezone.make_aware(end_datetime)
                            
                            now = timezone.now()
                            
                            if now >= end_datetime:

                                self._save_temporary_vehicle_to_history(vehicle_assignment)
                                
                                vehicle_assignment.temporary_vehicle_number = None
                                vehicle_assignment.temporary_vehicle_model = None
                                vehicle_assignment.temporary_vehicle_type = None
                                vehicle_assignment.temporary_vehicle_fuel_type = None
                                vehicle_assignment.temporary_vehicle_insurance_expiry_date = None
                                vehicle_assignment.temporary_vehicle_assigned_date = None
                                vehicle_assignment.temporary_vehicle_assigned_time = None
                                vehicle_assignment.temporary_vehicle_ending_date = None
                                vehicle_assignment.temporary_vehicle_ending_time = None
                                vehicle_assignment.temporary_vehicle_image = None
                                vehicle_assignment.note = None
                                vehicle_assignment.location = None
                                
                                vehicle_assignment.status = 'current_vehicle'
                                vehicle_assignment.save()
                                
                    except (ValueError, TypeError) as e:
                        print(f"DEBUG: Error parsing temporary vehicle end datetime: {e}")
                
                if vehicle_assignment.vehicle and vehicle_assignment.status == 'current_vehicle':
                    # Get today's date IN DUBAI
                    today_dubai = timezone.localtime(timezone.now(), dubai_tz).date()
                    
                    
                    # Create or get today's odometer reading
                    odometer_reading, created = DailyOdometerReading.objects.get_or_create(
                        vehicle=vehicle_assignment.vehicle,
                        reading_date=today_dubai,
                        defaults={'start_km': 0}
                    )
                
                serializer = VehicleDetailsSerializer(
                    vehicle_assignment, 
                    context={'request': request, 'dubai_tz': dubai_tz}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            except VehicleAssignment.DoesNotExist:
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
        
    def _save_temporary_vehicle_to_history(self, vehicle_assignment):
        """Save temporary vehicle details to history before clearing"""
        try:
            # Check if all required fields exist
            if not all([
                vehicle_assignment.temporary_vehicle_number,
                vehicle_assignment.temporary_vehicle_assigned_date,
                vehicle_assignment.temporary_vehicle_ending_date
            ]):
                return
            
            # Parse dates and times
            assigned_date = datetime.strptime(
                vehicle_assignment.temporary_vehicle_assigned_date, 
                '%Y-%m-%d'
            ).date() if vehicle_assignment.temporary_vehicle_assigned_date else None
            
            assigned_time = datetime.strptime(
                vehicle_assignment.temporary_vehicle_assigned_time, 
                '%H:%M'
            ).time() if vehicle_assignment.temporary_vehicle_assigned_time else None
            
            ending_date = datetime.strptime(
                vehicle_assignment.temporary_vehicle_ending_date, 
                '%Y-%m-%d'
            ).date() if vehicle_assignment.temporary_vehicle_ending_date else None
            
            ending_time = datetime.strptime(
                vehicle_assignment.temporary_vehicle_ending_time, 
                '%H:%M'
            ).time() if vehicle_assignment.temporary_vehicle_ending_time else None
            
            TemporaryVehicleHistory.objects.create(
                employee=vehicle_assignment.employee,
                vehicle_number=vehicle_assignment.temporary_vehicle_number,
                vehicle_model=vehicle_assignment.temporary_vehicle_model or '',
                vehicle_type=vehicle_assignment.temporary_vehicle_type,
                fuel_type=vehicle_assignment.temporary_vehicle_fuel_type,
                insurance_expiry_date=vehicle_assignment.temporary_vehicle_insurance_expiry_date,
                vehicle_image=vehicle_assignment.temporary_vehicle_image,
                assigned_date=assigned_date,
                assigned_time=assigned_time,
                ending_date=ending_date,
                ending_time=ending_time,
                note=vehicle_assignment.note,
                location=vehicle_assignment.location,
                status='expired'
            )
            
            print(f"Saved temporary vehicle history for {vehicle_assignment.employee.employeeId}")
            
        except Exception as e:
            print(f"Error saving temporary vehicle history: {e}")

        


class ReportVehicleIssueAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            try:
                vehicle_assignment = VehicleAssignment.objects.get(employee=user)
                current_vehicle = vehicle_assignment.vehicle
                
                if not current_vehicle:
                    return Response(
                        {"success": False, "error": "No vehicle assigned to this user"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate and save the issue
                serializer = ReportVehicleIssueSerializer(data=request.data)
                
                if serializer.is_valid():

                    dubai_tz = pytz.timezone('Asia/Dubai')
                    
                    # Get today's date in Dubai timezone
                    today_dubai = timezone.localtime(timezone.now(), dubai_tz).date()
                    
                    # Convert reported_date to Dubai timezone date for comparison
                    reported_date = serializer.validated_data['reported_date']
                    
                    # Check if reported_date is today (in Dubai time)
                    if reported_date == today_dubai:
                        # Check if user has checked in TODAY (Dubai date)
                        has_checked_in = AttendanceCheck.objects.filter(
                            employee=user,
                            check_date=today_dubai,  # Use Dubai date
                            check_type='in'
                        ).exists()
                        
                        if not has_checked_in:
                            return Response(
                                {"success": False, "error": "You need to check in first for today"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Check if user has already checked out TODAY (Dubai date)
                        has_checked_out = AttendanceCheck.objects.filter(
                            employee=user,
                            check_date=today_dubai,  # Use Dubai date
                            check_type='out'
                        ).exists()
                        
                        if has_checked_out:
                            return Response(
                                {"success": False, "error": "You have already checked out for today"},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                    # Create the issue with additional info
                    vehicle_issue = VehicleIssue.objects.create(
                        vehicle=current_vehicle,
                        title=serializer.validated_data['title'],
                        reported_date=serializer.validated_data['reported_date'],
                        status=serializer.validated_data['status'],
                        reported_by=user,
                        description=serializer.validated_data.get('description', ''),
                    )
                    
                    # Handle image upload if provided
                    if 'vehicle_issue_image' in request.FILES:
                        vehicle_issue.vehicle_issue_image = request.FILES['vehicle_issue_image']
                        vehicle_issue.save()
                    
                    # Return success response
                    return Response({
                        "success": True,
                        "message": "Vehicle issue reported successfully",
                        "issue_id": vehicle_issue.id,
                        "reported_date": vehicle_issue.reported_date,
                        "today_dubai": today_dubai.isoformat()  # For debugging
                    }, status=status.HTTP_201_CREATED)
                
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            except VehicleAssignment.DoesNotExist:
                return Response(
                    {"success": False, "error": "No vehicle assigned to this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"success": False, "error": f"Failed to report issue: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportVehicleDetailsIssueAPIView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request, issue_id):
        try:
            vehicle_issue = get_object_or_404(VehicleIssue, id=issue_id)
            serializer = ReportVehicleIssueSerializer(
                vehicle_issue,
                context={'request': request}
            )
            return Response({
                "success": True,
                "issue": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"success": False, "error": f"Failed to get issue details: {str(e)}"},
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

            dubai_tz = pytz.timezone('Asia/Dubai')
            
            # Get today's date in Dubai timezone
            today_dubai = timezone.localtime(timezone.now(), dubai_tz).date()
            
            # Parse the start date from the request
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"success": False, "error": "Invalid start date format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            

            # Only check attendance if temporary vehicle starts TODAY
            if start_date == today_dubai:
                # Check if user has checked in TODAY (Dubai date)
                has_checked_in = AttendanceCheck.objects.filter(
                    employee=user,
                    check_date=today_dubai,  # Use Dubai date
                    check_type='in'
                ).exists()
                
                if not has_checked_in:
                    return Response(
                        {"success": False, "error": "You need to check in first for today"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if user has already checked out TODAY (Dubai date)
                has_checked_out = AttendanceCheck.objects.filter(
                    employee=user,
                    check_date=today_dubai,  # Use Dubai date
                    check_type='out'
                ).exists()
                
                if has_checked_out:
                    return Response(
                        {"success": False, "error": "You have already checked out for today"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
 
            assignment, created = VehicleAssignment.objects.get_or_create(
                employee=user
            )
            
            assignment.temporary_vehicle_number = data['vehicle_number'].strip().upper()
            assignment.temporary_vehicle_model = data['vehicle_model'].strip()
            
            # Handle optional fields safely
            assignment.temporary_vehicle_type = data.get('vehicle_type', '').strip()
            assignment.temporary_vehicle_fuel_type = data.get('fuel_type', 'petrol')
            
            # Dates and times (stored as CharField in your model)
            assignment.temporary_vehicle_assigned_date = data['start_date']
            assignment.temporary_vehicle_assigned_time = data['start_time']
            assignment.temporary_vehicle_ending_date = data['end_date']
            assignment.temporary_vehicle_ending_time = data['end_time']
            
            # Optional fields
            assignment.note = data.get('add_note', '')
            assignment.location = data.get('location', '')

            # Handle image upload
            if 'vehicle_image' in request.FILES:
                assignment.temporary_vehicle_image = request.FILES['vehicle_image']

            assignment.status = 'temporary_vehicle'
            
            assignment.save()
            
            return Response(
                {
                    "success": True, 
                    "message": "Temporary vehicle assigned successfully.",
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )