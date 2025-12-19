# views.py
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import AttendanceCheck, BreakHistory, BreakTimer, CompanyAnnouncement, Employee, Leave
from .serializers import BreakSerializer, CheckInOutSerializer, CompanyAnnouncementSerializer, DetailedLeaveSerializer, EndBreakSerializer, HomeAPISerializer, LeaveCreateSerializer, LeaveDashboardSerializer, LeaveHistorySerializer
from django.shortcuts import get_object_or_404

class HomeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            employee = request.user
            serializer = HomeAPISerializer(employee)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckInAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CheckInOutSerializer(data=request.data, context={'is_checkout': False})
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user
            check_date = serializer.validated_data['check_date']

            existing_checkin = AttendanceCheck.objects.filter(
                employee=employee,
                check_type='in',
                check_date=check_date
            ).exists()
            
            if existing_checkin:
                return Response(
                    {"error": "Already checked in today"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reason = serializer.validated_data.get('reason')
            
            reason_to_store = reason if reason and str(reason).strip() != '' else None
            
            checkin = AttendanceCheck.objects.create(
                employee=employee,
                check_type='in',
                check_date=check_date,                 
                check_time=serializer.validated_data['check_time'],
                time_zone=serializer.validated_data['time_zone'],
                location=serializer.validated_data['location'],
                reason=reason_to_store,
            )
            
            return Response({
                "status": "success",
                "message": "Checked in successfully",
                "check_id": checkin.id,
                "check_date": checkin.check_date,
                "check_time": checkin.check_time,
                "time_zone": checkin.time_zone,
                "location": checkin.location,
                "reason_provided": reason_to_store is not None 
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



class CheckOutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CheckInOutSerializer(data=request.data, context={'is_checkout': True})
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user
            check_date = serializer.validated_data['check_date']

            checkin_today = AttendanceCheck.objects.filter(
                employee=employee,
                check_type='in',
                check_date=check_date
            ).exists()
            
            if not checkin_today:
                return Response(
                    {"error": "You need to check in first"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            existing_checkout = AttendanceCheck.objects.filter(
                employee=employee,
                check_type='out',
                check_date=check_date
            ).exists()
            
            if existing_checkout:
                return Response(
                    {"error": "Already checked out today"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            active_break = BreakTimer.objects.filter(
                employee=employee,
                break_end_time__isnull=True
            ).exists()
            
            if active_break:
                return Response(
                    {"error": "Please end your break before checking out"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create check-out record WITH reason (mandatory)
            checkout = AttendanceCheck.objects.create(
                employee=employee,
                check_type='out',
                check_date=serializer.validated_data['check_date'],
                check_time=serializer.validated_data['check_time'],
                time_zone=serializer.validated_data['time_zone'],
                location=serializer.validated_data['location'],
                reason=serializer.validated_data['reason']  
            )
            
            return Response({
                "status": "success",
                "message": "Checked out successfully",
                "check_id": checkout.id,
                "check_date": checkout.check_date,
                "check_time": checkout.check_time,
                "time_zone": checkout.time_zone,
                "location": checkout.location,
                "reason": checkout.reason
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartBreakAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BreakSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        employee = request.user
        today = serializer.validated_data['date']

        if not AttendanceCheck.objects.filter(
            employee=employee,
            check_date=today,
            check_type='in'
        ).exists():
            return Response(
                {"error": "You need to check in first"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if AttendanceCheck.objects.filter(
            employee=employee,
            check_date=today,
            check_type='out'
        ).exists():
            return Response(
                {"error": "You have already checked out for today"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if BreakTimer.objects.filter(
            employee=employee,
            date=today,
            break_end_time__isnull=True
        ).exists():
            return Response(
                {"error": "You already have an active break"},
                status=status.HTTP_400_BAD_REQUEST
            )

        break_data = {
            'employee': employee,
            'break_type': serializer.validated_data['break_type'],
            'duration': serializer.validated_data['duration'],
            'break_start_time': serializer.validated_data['break_start_time'],
            'date': today,
            'location': serializer.validated_data['location'],
        }

        if serializer.validated_data['break_type'] == 'other':
            break_data['custom_break_type'] = serializer.validated_data.get('custom_break_type')

        BreakTimer.objects.create(**break_data)

        return Response({
            "status": "success",
            "message": "Break started successfully",
        }, status=status.HTTP_201_CREATED)


class EndBreakAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EndBreakSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        employee = request.user
        today = serializer.validated_data['date']

        if AttendanceCheck.objects.filter(
            employee=employee,
            check_date=today,
            check_type='out'
        ).exists():
            return Response(
                {"error": "You have already checked out"},
                status=status.HTTP_400_BAD_REQUEST
            )

        active_break = BreakTimer.objects.filter(
            employee=employee,
            date=today,
            break_end_time__isnull=True
        ).first()

        if not active_break:
            return Response(
                {"error": "No active break found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = serializer.validated_data.get('end_reason')
        active_break.break_end_time = serializer.validated_data['break_end_time']
        active_break.end_reason = reason.strip() if reason and reason.strip() else None
        active_break.location = serializer.validated_data['location']
        active_break.save()

        return Response({
            "status": "success",
            "message": "Break ended successfully",
        }, status=status.HTTP_200_OK)
    

class CompanyAnnouncementListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            announcements = CompanyAnnouncement.objects.filter(
                is_active=True
            ).order_by('-date')
            
            serializer = CompanyAnnouncementSerializer(announcements, many=True)
            
            return Response({
                'status': 'success',
                'count': announcements.count(),
                'announcements': serializer.data
            })
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )            
        

import pytz
from datetime import timedelta
from django.db.models import Q, Sum

class LeaveDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get employee profile from authenticated user
            employee = request.user
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Set Dubai timezone
        dubai_tz = pytz.timezone('Asia/Dubai')
        now_dubai = timezone.now().astimezone(dubai_tz)
        
        # Calculate current month start and end in Dubai timezone
        current_month_start = now_dubai.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Get all leaves for the employee
        all_leaves = Leave.objects.filter(employee=employee)
        
        # 1. Calculate days left (assuming 30 days total vacation)
        total_vacation_days = 30  # This could be configured per employee
        
        # Calculate used vacation days (only approved leaves)
        approved_leaves = all_leaves.filter(
            status='approved',
            category='annual'  
        )
        print(approved_leaves, "approved")
        used_vacation_days = approved_leaves.aggregate(
            total=Sum('total_days')
        )['total'] or 0
        print(used_vacation_days, "vacation")
        days_left = total_vacation_days - used_vacation_days
        print(days_left, "vacation")

        # 2. Calculate leave taken this month (all categories, approved only)
        leave_this_month = all_leaves.filter(
            status='approved',
            created_at__gte=current_month_start,
            created_at__lte=current_month_end
        )
        leave_taken_this_month_count = leave_this_month.count()
        
        # 3. Calculate annual leave taken (approved annual leaves)
        annual_leave_taken_count = all_leaves.filter(
            status='approved',
            category='annual'
        ).count()
        
        # 4. Get recent leave requests (last 5, sorted by created date)
        # Only show PENDING requests in leave_requests section
        recent_requests = all_leaves.filter(
            status='pending'
        ).order_by('-created_at')[:5]
        
        # 5. Get all leave history
        # Show only APPROVED, REJECTED, or CANCELLED leaves in history (not pending)
        all_history = all_leaves.filter(
            Q(status='approved') | Q(status='rejected') | Q(status='cancelled')
        ).order_by('-created_at')
        
        # Serialize the data
        dashboard_data = {
            'days_left': days_left,
            'total_vacation_days': total_vacation_days,
            'used_vacation_days': used_vacation_days,
            'leave_taken_this_month': leave_taken_this_month_count,
            'annual_leave_taken': annual_leave_taken_count,
            'leave_requests': recent_requests,  # Only pending
            'leave_history': all_history  # Only non-pending (approved/rejected/cancelled)
        }
        
        serializer = LeaveDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    


class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, leave_id):
        try:
            # Get the authenticated user's employee profile
            employee = request.user
            
            # Get the specific leave for this employee
            leave = get_object_or_404(Leave, id=leave_id, employee=employee)
            
            # Serialize the leave data
            serializer = DetailedLeaveSerializer(leave, context={'request': request})
            
            return Response({
                "success": True,
                "message": "Leave details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Employee profile not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Leave.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Leave application not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )



from rest_framework.parsers import MultiPartParser, FormParser


class LeaveApplicationView(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        try:
            employee = request.user
        except Employee.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Employee profile not found. Please complete your profile."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if employee is active
        if not employee.is_active:
            return Response(
                {
                    "success": False,
                    "error": "Your account is not active. Please contact HR."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare data for serializer
        data = request.data.copy()
        data['employee'] = employee.id
        
        # Validate and create leave application
        serializer = LeaveCreateSerializer(data=data)
        
        if serializer.is_valid():
            # Create the leave application
            try:
                leave = serializer.save(
                    employee=employee,
                    status='pending'  # Default status
                )
                
                return Response({
                    "success": True,
                    "message": "Leave application submitted successfully!",
                    "next_steps": "Your leave application is pending approval. You will be notified once it's reviewed."
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    "success": False,
                    "error": f"Error creating leave application: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            # Return validation errors
            errors = serializer.errors
            
            # Format errors for better readability
            formatted_errors = {}
            for field, error_list in errors.items():
                if isinstance(error_list, list):
                    formatted_errors[field] = error_list[0] if error_list else "Invalid value"
                else:
                    formatted_errors[field] = str(error_list)
            
            return Response({
                "success": False,
                "error": "Validation failed",
                "details": formatted_errors
            }, status=status.HTTP_400_BAD_REQUEST)



