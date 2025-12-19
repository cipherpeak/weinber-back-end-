from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Note
from authapp.models import Employee
from .serializers import (
    NoteSerializer, 
    NoteCreateSerializer, 
    NoteDetailSerializer
)


class NoteListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all notes for the authenticated employee"""
        try:
            employee = request.user
            
            # Get all notes for this employee
            notes = Note.objects.filter(employee=employee).order_by('-created_at')
            
            # Serialize the data
            serializer = NoteSerializer(notes, many=True)
            
            return Response({
                "success": True,
                "message": "Notes retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error retrieving notes: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new note"""
        try:
            employee = request.user
            
            # Validate and create the note
            serializer = NoteCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                # Create note with employee association
                note = Note.objects.create(
                    employee=employee,
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data['description'],
                    date=serializer.validated_data['date']
                )
                
                return Response({
                    "success": True,
                    "message": "Note created successfully",
                }, status=status.HTTP_201_CREATED)
            else:
                # Return validation errors
                return Response({
                    "success": False,
                    "error": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error creating note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NoteDetailView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get_note(self, note_id, employee):
        """Helper method to get note with permission check"""
        try:
            note = Note.objects.get(id=note_id, employee=employee)
            return note
        except Note.DoesNotExist:
            return None
    
    def get(self, request, note_id):
        """Get details of a specific note"""
        try:
            employee =request.user
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to view it"
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = NoteDetailSerializer(note)
            
            return Response({
                "success": True,
                "message": "Note details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error retrieving note details: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, note_id):
        """Update a note"""
        try:
            employee = Employee.objects.get(user=request.user)
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to edit it"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate and update the note
            serializer = NoteCreateSerializer(data=request.data, partial=True)
            
            if serializer.is_valid():
                # Update note fields
                if 'title' in serializer.validated_data:
                    note.title = serializer.validated_data['title']
                if 'description' in serializer.validated_data:
                    note.description = serializer.validated_data['description']
                if 'date' in serializer.validated_data:
                    note.date = serializer.validated_data['date']
                
                note.save()
                
                # Return the updated note
                response_serializer = NoteSerializer(note)
                
                return Response({
                    "success": True,
                    "message": "Note updated successfully",
                    "data": response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Return validation errors
                return Response({
                    "success": False,
                    "error": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error updating note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, note_id):
        """Delete a note"""
        try:
            employee = Employee.objects.get(user=request.user)
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to delete it"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete the note
            note_id = note.id
            note_title = note.title
            note.delete()
            
            return Response({
                "success": True,
                "message": f"Note '{note_title}' deleted successfully",
                "deleted_note_id": note_id
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error deleting note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NoteSearchView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search notes by keyword"""
        try:
            employee = Employee.objects.get(user=request.user)
            search_query = request.GET.get('q', '').strip()
            
            if not search_query:
                return Response({
                    "success": False,
                    "error": "Search query is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Search in title and description
            notes = Note.objects.filter(
                employee=employee
            ).filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            ).order_by('-created_at')
            
            # Serialize the data
            serializer = NoteSerializer(notes, many=True)
            
            return Response({
                "success": True,
                "message": f"Found {notes.count()} notes matching '{search_query}'",
                "search_query": search_query,
                "count": notes.count(),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error searching notes: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class NoteEditView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get_note(self, note_id, employee):
        try:
            note = Note.objects.get(id=note_id, employee=employee)
            return note
        except Note.DoesNotExist:
            return None
    
    def put(self, request, note_id):

        try:
            # Get the authenticated employee
            employee = request.user
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to edit it"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the incoming data (all fields required for PUT)
            serializer = NoteCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                # Update note with new data
                note.title = serializer.validated_data['title']
                note.description = serializer.validated_data['description']
                note.date = serializer.validated_data['date']
                note.save()
                
                # Return the updated note
                response_serializer = NoteSerializer(note)
                
                return Response({
                    "success": True,
                    "message": "Note updated successfully",
                }, status=status.HTTP_200_OK)
            else:
                # Return validation errors
                return Response({
                    "success": False,
                    "error": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error updating note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, note_id):

        try:
            # Get the authenticated employee
            employee = Employee.objects.get(user=request.user)
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to edit it"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the incoming data (partial update)
            serializer = NoteCreateSerializer(data=request.data, partial=True)
            
            if serializer.is_valid():
                # Update only the fields that are provided
                if 'title' in serializer.validated_data:
                    note.title = serializer.validated_data['title']
                if 'description' in serializer.validated_data:
                    note.description = serializer.validated_data['description']
                if 'date' in serializer.validated_data:
                    note.date = serializer.validated_data['date']
                
                note.save()
                
                # Return the updated note
                response_serializer = NoteSerializer(note)
                
                return Response({
                    "success": True,
                    "message": "Note updated successfully",
                    "data": response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Return validation errors
                return Response({
                    "success": False,
                    "error": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error updating note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NoteDeleteView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get_note(self, note_id, employee):
        """Helper method to get note with permission check"""
        try:
            note = Note.objects.get(id=note_id, employee=employee)
            return note
        except Note.DoesNotExist:
            return None
    
    def delete(self, request, note_id):

        try:
            # Get the authenticated employee
            employee = request.user
            
            # Get the note
            note = self.get_note(note_id, employee)
            
            if not note:
                return Response({
                    "success": False,
                    "error": "Note not found or you don't have permission to delete it"
                }, status=status.HTTP_404_NOT_FOUND)
            

            note_title = note.title
            
            # Delete the note
            note.delete()
            
            return Response({
                "success": True,
                "message": f"Note '{note_title}' deleted successfully",
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                "success": False,
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error deleting note: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




