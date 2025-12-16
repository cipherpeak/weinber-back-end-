from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import VisaDetails
from .serializers import DocumentUpdateSerializer, EmployeeInformationSerializer, EmployeePersonalInfoSerializer, EmployeePersonalInfoUpdateSerializer, EmployeeProfileSerializer, VisaDetailsSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class EmployeeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user
            
            serializer = EmployeeProfileSerializer(employee)
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