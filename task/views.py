from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db.models import Q
from .models import Task, TaskDuty, TaskProgressImage
from .serializers import PendingQueueSerializer, PendingTaskSerializer, SaveProgressSerializer, TaskDetailSerializer, TaskDetailsResponseSerializer, TaskListSerializer
from django.shortcuts import get_object_or_404

class TaskListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            today = timezone.now().date()    
            try:
                user = request.user
                tasks = Task.objects.filter(
                    employee=user,
                    task_assign_time__date=today 
                )
            except AttributeError:
                return Response({
                    'tasks': []
                }, status=status.HTTP_200_OK)
            
            status_filter = request.query_params.get('status')
            task_type_filter = request.query_params.get('task_type')
            icon_type_filter = request.query_params.get('icon_type')
            
            if status_filter:
                tasks = tasks.filter(status=status_filter)
            if task_type_filter:
                tasks = tasks.filter(task_type=task_type_filter)
            if icon_type_filter:
                tasks = tasks.filter(icon_type=icon_type_filter)
            
            tasks = tasks.order_by('task_assign_time')
            
            serializer = TaskListSerializer(tasks, many=True)
            
            return Response({
                'tasks': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error retrieving tasks: {str(e)}',
                'tasks': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class TaskDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, task_id):
        try:
            user = request.user
            
            task = get_object_or_404(
                Task, 
                id=task_id, 
                employee=user
            )
            
            serializer = TaskDetailSerializer(task)
            
            return Response({
                'success': True,
                'task': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Task.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Task not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error retrieving task details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class StartTaskAPIView(APIView):
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            
            if task.status == 'in_progress':
                return Response(
                    {"error": "Task is already in progress"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if task.status in ['completed', 'delivered']:
                return Response(
                    {"error": f"Cannot start task that is already {task.status}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            task.status = 'in_progress'
            task.task_start_time = timezone.now()
            task.save()
            
            return Response(
                {"message": "task started"},
                status=status.HTTP_200_OK
            )
            
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


class StartTaskDetailsAPIView(APIView):
    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        
            serializer = TaskDetailsResponseSerializer(
                task, 
                context={'request': request}
            )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    




class SaveTaskProgressAPIView(APIView):
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            
            serializer = SaveProgressSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            
            # Update duty completion status
            all_duties_completed = self._update_duties(task, data['duty_list'])
            
            # Save progress image if provided
            if data.get('image'):
                TaskProgressImage.objects.create(
                    task=task,
                    image=data['image'],
                    percentage_completed=data['percentage']
                )
            
            # Update task progress
            task.percentage_completed = data['percentage']
            task.task_notes = data.get('progress_notes', '') or task.task_notes
            
            # Check if all duties are completed
            if all_duties_completed:
                task.status = 'completed'
                task.task_completed_date = timezone.now()
                task.task_notes = data.get('final_notes', '') or task.task_notes
                task.save()
                
                return Response(
                    {"message": "task completed"},
                    status=status.HTTP_200_OK
                )
            else:
                task.save()
                
                return Response(
                    {"message": "saved progress"},
                    status=status.HTTP_200_OK
                )
            
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _update_duties(self, task, duty_list):
        """
        Update duty completion status and return True if all duties are completed
        """
        all_completed = True
        
        for duty_data in duty_list:
            try:
                duty_id = duty_data.get('id')
                is_completed = duty_data.get('is_completed', False)
                
                if duty_id:
                    task_duty = TaskDuty.objects.get(id=duty_id, task=task)
                    task_duty.is_completed = is_completed
                    
                    # Set completion time if duty is being marked as completed
                    if is_completed and not task_duty.completed_at:
                        task_duty.completed_at = timezone.now()
                    elif not is_completed:
                        task_duty.completed_at = None
                    
                    task_duty.save()
                    
                    # Check if this duty is completed
                    if not is_completed:
                        all_completed = False
                        
            except TaskDuty.DoesNotExist:
                continue
            except Exception as e:
                # Log error but continue with other duties
                print(f"Error updating duty {duty_id}: {str(e)}")
                all_completed = False
        
        return all_completed
    



class PendingTasksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            today = timezone.now().date()
            
           
            pending_tasks = Task.objects.filter(
                employee=user,
                status__in=['not_started', 'paused', 'in_progress', 'on_hold'],
                task_assign_time__date__lte=today  
            ).exclude(
                status__in=['completed', 'delivered', 'returned']
            ).order_by('task_assign_time')


            status_filter = request.query_params.get('status')
            task_type_filter = request.query_params.get('task_type')
            icon_type_filter = request.query_params.get('icon_type')
            
            if status_filter:
                pending_tasks = pending_tasks.filter(status=status_filter)
            if task_type_filter:
                pending_tasks = pending_tasks.filter(task_type=task_type_filter)
            if icon_type_filter:
                pending_tasks = pending_tasks.filter(icon_type=icon_type_filter)
            
            pending_task_list = pending_tasks.filter(
                Q(status='in_progress') | Q(percentage_completed__gt=0)
            )
            
            pending_queue_list = pending_tasks.filter(
                Q(status__in=['not_started', 'paused', 'on_hold']) & Q(percentage_completed=0)
            )
            
            # Serialize data
            pending_tasks_serializer = PendingTaskSerializer(pending_task_list, many=True)
            pending_queue_serializer = PendingQueueSerializer(pending_queue_list, many=True)
            
            response_data = {
                'pending_task': pending_tasks_serializer.data,
                'pending_queue': pending_queue_serializer.data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error retrieving pending tasks: {str(e)}',
                'pending_task': [],
                'pending_queue': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
