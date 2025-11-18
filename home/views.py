# views.py
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import AttendanceCheck, BreakHistory, BreakTimer, CompanyAnnouncement, Employee
from .serializers import BreakSerializer, CheckInOutSerializer, CompanyAnnouncementSerializer, HomeAPISerializer

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
            today = timezone.now().date()
            
            existing_checkin = AttendanceCheck.objects.filter(
                employee=employee,
                check_date=today,
                check_type='in'
            ).exists()
            
            if existing_checkin:
                return Response(
                    {"error": "Already checked in today"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create check-in record
            checkin = AttendanceCheck.objects.create(
                employee=employee,
                check_type='in',
                check_date=today,
                check_time=serializer.validated_data['check_time'],
                time_zone=serializer.validated_data['time_zone'],
                location=serializer.validated_data['location']
                # No reason for check-in
            )
            
            return Response({
                "status": "success",
                "message": "Checked in successfully",
                "check_id": checkin.id,
                "check_date": str(checkin.check_date),
                "check_time": checkin.check_time,
                "time_zone": checkin.time_zone,
                "location": checkin.location
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
            today = timezone.now().date()
            
            # Check if user has checked in today
            checkin_today = AttendanceCheck.objects.filter(
                employee=employee,
                check_date=today,
                check_type='in'
            ).exists()
            
            if not checkin_today:
                return Response(
                    {"error": "You need to check in first"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already checked out today
            existing_checkout = AttendanceCheck.objects.filter(
                employee=employee,
                check_date=today,
                check_type='out'
            ).exists()
            
            if existing_checkout:
                return Response(
                    {"error": "Already checked out today"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there's an active break (break without end time)
            active_break = BreakTimer.objects.filter(
                employee=employee,
                date=today,
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
                check_date=today,
                check_time=serializer.validated_data['check_time'],
                time_zone=serializer.validated_data['time_zone'],
                location=serializer.validated_data['location'],
                reason=serializer.validated_data['reason']  # Reason is mandatory for checkout
            )
            
            return Response({
                "status": "success",
                "message": "Checked out successfully",
                "check_id": checkout.id,
                "check_date": str(checkout.check_date),
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
        try:
            serializer = BreakSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user
            today = timezone.now().date()
            
            # Check if checked in today
            checkin_today = AttendanceCheck.objects.filter(
                employee=employee,
                check_time__date=today,
                check_type='in'
            ).exists()
            
            if not checkin_today:
                return Response(
                    {"error": "You need to check in first"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already checked out today
            checkout_today = AttendanceCheck.objects.filter(
                employee=employee,
                check_time__date=today,
                check_type='out'
            ).exists()
            
            if checkout_today:
                return Response(
                    {"error": "You have already checked out for today"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there's already an active break (break without end time)
            active_break = BreakTimer.objects.filter(
                employee=employee,
                date=today,
                break_end_time__isnull=True
            ).exists()
            
            if active_break:
                return Response(
                    {"error": "You already have an active break"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create break record WITH reason
            break_timer = BreakTimer.objects.create(
                employee=employee,
                break_type=serializer.validated_data['break_type'],
                break_start_time=timezone.now(),
                date=today,
                duration=timezone.timedelta(0),
                reason=serializer.validated_data.get('reason', '')  
            )
            
            return Response({
                "status": "success",
                "message": "Break started successfully",
                "break_type": break_timer.break_type,
                "break_start_time": break_timer.break_start_time,
                "location": serializer.validated_data['location'],
                "reason": break_timer.reason  # Include reason in response
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EndBreakAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # For end break, we don't need reason, only location
            location = request.data.get('location', '')
            if not location:
                return Response(
                    {"error": "Location is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user
            today = timezone.now().date()
            
            # Get active break (break without end time)
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
            
            # Calculate duration and update break
            end_time = timezone.now()
            duration = end_time - active_break.break_start_time
            
            active_break.break_end_time = end_time
            active_break.duration = duration
            active_break.save()
            
            # Update break history
            self.update_break_history(employee, today, active_break.break_type, duration)
            
            return Response({
                "status": "success",
                "message": "Break ended successfully",
                "break_type": active_break.break_type,
                "break_start_time": active_break.break_start_time,
                "break_end_time": active_break.break_end_time,
                "duration": str(duration),
                "location": location,
                "reason": active_break.reason  # Return the reason from start
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update_break_history(self, employee, date, break_type, duration):
        """Update break history for the employee"""
        break_history, created = BreakHistory.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'total_break_time': duration,
                'number_of_scheduled_breaks': 1 if break_type == 'scheduled' else 0
            }
        )
        
        if not created:
            break_history.total_break_time += duration
            if break_type == 'scheduled':
                break_history.number_of_scheduled_breaks += 1
            break_history.save()
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CheckInOutSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = request.user
            today = timezone.now().date()
            
            # Get active break (break without end time)
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
            
            # Calculate duration and update break
            end_time = timezone.now()
            duration = end_time - active_break.break_start_time
            
            active_break.break_end_time = end_time
            active_break.duration = duration
            active_break.save()
            
            # Update break history
            self.update_break_history(employee, today, active_break.break_type, duration)
            
            return Response({
                "status": "success",
                "message": "Break ended successfully",
                "break_type": active_break.break_type,
                "break_start_time": active_break.break_start_time,
                "break_end_time": active_break.break_end_time,
                "duration": str(duration),
                "location": serializer.validated_data['location']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update_break_history(self, employee, date, break_type, duration):
        """Update break history for the employee"""
        break_history, created = BreakHistory.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'total_break_time': duration,
                'number_of_scheduled_breaks': 1 if break_type == 'scheduled' else 0
            }
        )
        
        if not created:
            break_history.total_break_time += duration
            if break_type == 'scheduled':
                break_history.number_of_scheduled_breaks += 1
            break_history.save()


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