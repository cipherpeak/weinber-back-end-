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