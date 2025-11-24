# views.py
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import AttendanceCheck, BreakHistory, BreakTimer, CompanyAnnouncement, Employee
from .serializers import BreakSerializer, CheckInOutSerializer, CompanyAnnouncementSerializer, EndBreakSerializer, HomeAPISerializer

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
            
            reason = serializer.validated_data.get('reason')
            
            reason_to_store = reason if reason and str(reason).strip() != '' else None
            
            checkin = AttendanceCheck.objects.create(
                employee=employee,
                check_type='in',
                check_date=today,
                check_time=serializer.validated_data['check_time'],
                time_zone=serializer.validated_data['time_zone'],
                location=serializer.validated_data['location'],
                reason=reason_to_store, 
            )
            
            return Response({
                "status": "success",
                "message": "Checked in successfully",
                "check_id": checkin.id,
                "check_date": str(checkin.check_date),
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
                check_date=today,
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
                check_date=today,
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
            
            break_data = {
                'employee': employee,
                'break_type': serializer.validated_data['break_type'],
                'duration': serializer.validated_data['duration'],
                'break_start_time': serializer.validated_data['break_start_time'],
                'date': today,  
                'location': serializer.validated_data['location'],
                'reason': serializer.validated_data.get('reason', '')
            }
            
            # Add custom break type if provided
            if serializer.validated_data['break_type'] == '':
                break_data['custom_break_type'] = serializer.validated_data.get('custom_break_type', '')
            
            break_timer = BreakTimer.objects.create(**break_data)
            
            return Response({
                "status": "success",
                "message": "Break started successfully",
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
            serializer = EndBreakSerializer(data=request.data)
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
            
            active_break.break_end_time = serializer.validated_data['break_end_time']
            active_break.location = serializer.validated_data['location']
            active_break.end_reason = serializer.validated_data.get('end_reason', '')  
            active_break.save()
            
            return Response({
                "status": "success",
                "message": "Break ended successfully",
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
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