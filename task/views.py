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
            company = getattr(user, 'company', None)
            print(company,"this is")
            # Get the task for this user
            task = get_object_or_404(
                Task, 
                id=task_id, 
                employee=user
            )
            print(task,"this is task")

            if company == 'dax':
                print("am i in")
                return self._get_dax_task_details(request, task)
            elif company == 'advantage':
                return self._get_advantage_task_details(request, task)
            elif company in ['v2', 'velux']:
                return self._get_advantage_task_details(request, task)
            else:
                # Default response for users without company or unknown company
                return self._get_advantage_task_details(request, task)
                
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
    
    def _get_dax_task_details(self, request, task):
        print("insed daxxxxxxxxxxx")
        """Get task details for DAX company"""
        try:
            # Get related ServiceTaskDax object for this task
            service_dax = ServiceTaskDax.objects.filter(task=task).first()
            print(service_dax,"checking")
            if not service_dax:
                return Response({
                    'success': False,
                    'error': 'No DAX service task found for this task'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get progress images for this task
            progress_images = []
            for img in task.progress_images.all():
                progress_images.append({
                    "image": request.build_absolute_uri(img.image.url) if img.image else None,
                    "date": img.created_at.isoformat() if img.created_at else None
                })
            
            # Get vehicle make/model from vehicle_details if available
            vehicle_make_model = None
            if task.vehicle_details:
                try:
                    details = task.vehicle_details.split(',')
                    if len(details) >= 1:
                        vehicle_make_model = details[0].strip()
                except:
                    pass
            
            # Format dates properly
            def format_datetime(dt):
                if dt:
                    return dt.isoformat()
                return None
            
            def format_date(d):
                if d:
                    return d.isoformat()
                return None
            
            # Prepare task object with all fields properly serialized
            task_data = {
                "id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "due_date": format_datetime(task.due_date),
                "vehicle_details": task.vehicle_details,
                "vehicle_model": task.vehicle_model,
                "vehicle_year": task.vehicle_year,
                "vehicle_color": task.vehicle_color,
                "customer_name": task.customer_name,
                "address": task.address,
                "priority": task.priority,
                "location": task.location,
                "percentage_completed": task.percentage_completed,
                "task_assign_time": format_datetime(task.task_assign_time),
                "task_start_time": format_datetime(task.task_start_time),
                "task_completed_date": format_datetime(task.task_completed_date),
                "description": task.description,
                "task_notes": task.task_notes,
                "icon_type": task.icon_type,
                "is_nothing_task": task.is_nothing_task,
            }
            
            # Prepare service dax object with all fields properly serialized
            service_dax_data = {
                "id": str(service_dax.id),
                "task": task_data,
                "detailing_site": service_dax.detailing_site,
                "detailing_site_display": service_dax.get_detailing_site_display(),
                "other_site_name": service_dax.other_site_name,
                "service_type": service_dax.service_type,
                "service_type_display": service_dax.get_service_type_display(),
                "tinting_type": service_dax.tinting_type,
                "tinting_percentage": service_dax.tinting_percentage,
                "tinting_custom_text": service_dax.tinting_custom_text,
                "coating_layers": service_dax.coating_layers or [],
                "coating_layers_display": service_dax.get_coating_layers_display(),
                "ppf_type": service_dax.ppf_type,
                "ppf_custom_text": service_dax.ppf_custom_text,
                "remarks": service_dax.remarks,
                "chassis_no": service_dax.chassis_no,
                "vehicle_make_model": vehicle_make_model,
                "invoice_status": service_dax.invoice_status,
                "invoice_status_display": service_dax.get_invoice_status_display() if service_dax.invoice_status else None,
                "invoice_pri_image": request.build_absolute_uri(service_dax.invoice_pri_image.url) if service_dax.invoice_pri_image else None,
                "vehicle_progress_image": progress_images,
                "work_location": service_dax.work_location,
                "shared_staff_details": service_dax.shared_staff_details,
                "created_at": format_datetime(service_dax.created_at),
                "updated_at": format_datetime(service_dax.updated_at)
            }
            
            return Response({
                'success': True,
                'company': 'dax',
                'task_details': service_dax_data
            }, status=status.HTTP_200_OK)
            
        except ServiceTaskDax.DoesNotExist:
            return Response({
                'success': False,
                'error': 'DAX service task not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error retrieving DAX task details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_advantage_task_details(self, request, task):
        """Get task details for Advantage company"""
        print("insed advantageeeeeee")

        try:
            # Serialize task data properly
            task_data = {
                "id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "vehicle_details": task.vehicle_details,
                "customer_name": task.customer_name,
                "location": task.location,
                "priority": task.priority,
                "description": task.description,
                "task_notes": task.task_notes,
            }
            
            advantage_data = {
                'company': 'advantage',
                'task_id': str(task.id),
                'basic_task_info': task_data,
                'advantage_specific_fields': {
                    'service_type': 'advantage_service',
                    'location_type': 'commercial',
                }
            }
            
            return Response({
                'success': True,
                'company': 'advantage',
                'task_details': advantage_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error retrieving Advantage task details: {str(e)}'
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
        



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ServiceTaskDax, Task
from .serializers import ServiceTaskDaxSerializer
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
import json

class ServiceTaskDAXListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get query parameters
            employee_id = request.query_params.get('employee_id')
            task_type = request.query_params.get('task_type')
            status_filter = request.query_params.get('status')
            date_filter = request.query_params.get('date')
            
            # Start with all ServiceTaskDax objects
            queryset = ServiceTaskDax.objects.select_related(
                'task', 
                'task__employee'
            ).prefetch_related(
                'task__progress_images'
            ).all()
            
            # Apply filters based on query parameters
            if employee_id:
                queryset = queryset.filter(task__employee__id=employee_id)
            
            if task_type:
                queryset = queryset.filter(task__task_type=task_type)
            
            if status_filter:
                queryset = queryset.filter(task__status=status_filter)
            
            if date_filter:
                # Assuming date_filter is in YYYY-MM-DD format
                queryset = queryset.filter(task__due_date__date=date_filter)
            
            # Order by creation date (newest first)
            queryset = queryset.order_by('-created_at')
            
            # Prepare response data
            data = []
            for service_dax in queryset:
                task = service_dax.task
                
                # Get progress images for this task
                progress_images = []
                for img in task.progress_images.all():
                    progress_images.append({
                        "image": request.build_absolute_uri(img.image.url) if img.image else None,
                        "date": img.created_at.isoformat() if img.created_at else None
                    })
                
                # Get vehicle make/model from vehicle_details if available
                vehicle_make_model = None
                if task.vehicle_details:
                    try:
                        # Assuming vehicle_details might contain make/model info
                        # You might need to parse this differently based on your actual data structure
                        details = task.vehicle_details.split(',')
                        if len(details) >= 1:
                            vehicle_make_model = details[0].strip()
                    except:
                        pass
                
                # Format due_date if exists
                due_date = None
                if task.due_date:
                    due_date = task.due_date.isoformat()
                
                # Prepare task object
                task_data = {
                    "task_type": task.task_type,
                    "status": task.status,
                    "due_date": due_date,
                    "vehicle_details": task.vehicle_details,
                    "vehicle_model": task.vehicle_model,
                    "vehicle_year": task.vehicle_year,
                    "vehicle_color": task.vehicle_color,
                    "customer_name": task.customer_name,
                    "address": task.address,
                    "priority": task.priority,
                    "location": task.location,
                    "percentage_completed": task.percentage_completed,
                    "task_assign_time": task.task_assign_time.isoformat() if task.task_assign_time else None,
                    "task_start_time": task.task_start_time.isoformat() if task.task_start_time else None,
                    "task_completed_date": task.task_completed_date.isoformat() if task.task_completed_date else None,
                    "description": task.description,
                    "task_notes": task.task_notes,
                    "icon_type": task.icon_type,
                    "is_nothing_task": task.is_nothing_task,
                }
                
                
                # Prepare service dax object
                service_dax_data = {
                    "id": service_dax.id,
                    "task": task_data,
                    "detailing_site": service_dax.detailing_site,
                    "other_site_name": service_dax.other_site_name,
                    "service_type": service_dax.service_type,
                    "tinting_type": service_dax.tinting_type,
                    "tinting_percentage": service_dax.tinting_percentage,
                    "tinting_custom_text": service_dax.tinting_custom_text,
                    "coating_layers": service_dax.coating_layers or [],
                    "ppf_type": service_dax.ppf_type,
                    "ppf_custom_text": service_dax.ppf_custom_text,
                    "remarks": service_dax.remarks,
                    "chassis_no": service_dax.chassis_no,
                    "vehicle_make_model": vehicle_make_model,
                    "invoice_status": service_dax.invoice_status,
                    "invoice_pri_image": request.build_absolute_uri(service_dax.invoice_pri_image.url) if service_dax.invoice_pri_image else None,
                    "vehicle_progress_image": progress_images,
                    "work_location": service_dax.work_location,
                    "shared_staff_details": service_dax.shared_staff_details,
                    "created_at": service_dax.created_at.isoformat() if service_dax.created_at else None,
                    "updated_at": service_dax.updated_at.isoformat() if service_dax.updated_at else None
                }
                
                data.append(service_dax_data)
            
            # Prepare final response
            response = {
                "status": "success",
                "data": data,
                "count": len(data),
                "message": "Service tasks retrieved successfully"
            }
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e),
                "data": [],
                "count": 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceTaskDAXDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            # Get specific ServiceTaskDax by ID
            service_dax = ServiceTaskDax.objects.select_related(
                'task', 
                'task__employee'
            ).prefetch_related(
                'task__progress_images'
            ).get(id=pk)
            
            task = service_dax.task
            
            # Get progress images for this task
            progress_images = []
            for img in task.progress_images.all():
                progress_images.append({
                    "image": request.build_absolute_uri(img.image.url) if img.image else None,
                    "date": img.created_at.isoformat() if img.created_at else None
                })
            
            vehicle_make_model = None
            if task.vehicle_details:
                try:
                    details = task.vehicle_details.split(',')
                    if len(details) >= 1:
                        vehicle_make_model = details[0].strip()
                except:
                    pass
            
            # Format due_date if exists
            due_date = None
            if task.due_date:
                due_date = task.due_date.isoformat()
            
            # Prepare task object
            task_data = {
                "task_type": task.task_type,
                "status": task.status,
                "due_date": due_date,
                "vehicle_details": task.vehicle_details,
                "vehicle_model": task.vehicle_model,
                "vehicle_year": task.vehicle_year,
                "vehicle_color": task.vehicle_color,
                "customer_name": task.customer_name,
                "address": task.address,
                "priority": task.priority,
                "location": task.location,
                "percentage_completed": task.percentage_completed,
                "heading": task.heading,
                "employee_id": task.employee.employeeId if task.employee else None,
                "task_assign_time": task.task_assign_time.isoformat() if task.task_assign_time else None,
                "task_start_time": task.task_start_time.isoformat() if task.task_start_time else None,
                "task_completed_date": task.task_completed_date.isoformat() if task.task_completed_date else None,
                "description": task.description,
                "task_notes": task.task_notes,
                "icon_type": task.icon_type,
                "is_nothing_task": task.is_nothing_task,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
            
            # Get display values for choices
            detailing_site_display = service_dax.get_detailing_site_display()
            service_type_display = dict(ServiceTaskDax.SERVICES_CHOICES).get(service_dax.service_type, service_dax.service_type)
            coating_layers_display = service_dax.get_coating_layers_display()
            
            # Prepare service dax object
            data = {
                "id": service_dax.id,
                "task": task_data,
                "detailing_site": service_dax.detailing_site,
                "detailing_site_display": detailing_site_display,
                "other_site_name": service_dax.other_site_name,
                "service_type": service_dax.service_type,
                "service_type_display": service_type_display,
                "tinting_type": service_dax.tinting_type,
                "tinting_percentage": service_dax.tinting_percentage,
                "tinting_custom_text": service_dax.tinting_custom_text,
                "coating_layers": service_dax.coating_layers or [],
                "coating_layers_display": coating_layers_display,
                "ppf_type": service_dax.ppf_type,
                "ppf_custom_text": service_dax.ppf_custom_text,
                "remarks": service_dax.remarks,
                "chassis_no": service_dax.chassis_no,
                "vehicle_make_model": vehicle_make_model,
                "invoice_status": service_dax.invoice_status,
                "invoice_pri_image": request.build_absolute_uri(service_dax.invoice_pri_image.url) if service_dax.invoice_pri_image else None,
                "vehicle_progress_image": progress_images,
                "work_location": service_dax.work_location,
                "shared_staff_details": service_dax.shared_staff_details,
                "created_at": service_dax.created_at.isoformat() if service_dax.created_at else None,
                "updated_at": service_dax.updated_at.isoformat() if service_dax.updated_at else None
            }
            
            response = {
                "status": "success",
                "data": data,
                "message": "Service task details retrieved successfully"
            }
            
            return Response(response, status=status.HTTP_200_OK)
            
        except ServiceTaskDax.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Service task not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
