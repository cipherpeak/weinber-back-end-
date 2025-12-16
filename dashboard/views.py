from django.shortcuts import render, redirect,get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from authapp.models import Employee
from home.models import AttendanceCheck, BreakTimer, CompanyAnnouncement,Leave
from profileapp.models import Document, VisaDetails
from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from datetime import datetime, timedelta,date
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth
from django.core.mail import send_mail
from django.conf import settings
from task.models import Task, DeliveryTask, OfficeTask, ServiceTask, TaskDuty, TaskProgressImage


class AdminLogin(View):
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')
    
    @method_decorator(never_cache)
    def post(self, request):
        # Get form data
        login_input = request.POST.get('email') 
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=login_input, password=password)
        
        if user is None:
            try:
                user_obj = Employee.objects.get(email=login_input)
                user = authenticate(request, username=user_obj.employeeId, password=password)
            except Employee.DoesNotExist:
                user = None
        
        if user is not None:
            if self.can_user_login(user):
                login(request, user)
                
                if not remember_me:
                    request.session.set_expiry(0)
                
                # Store user info in session if needed
                request.session['user_full_name'] = user.get_full_name()
                if hasattr(user, 'employee'):
                    request.session['profile_image'] = user.employee.profile_image.url if user.employee.profile_image else None
                
                messages.success(request, 'Login successful!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Access denied. Only admin users are allowed to login.')
                return render(request, 'login.html')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'login.html')
    
    def can_user_login(self, user):
        """
        Check if user is allowed to login
        Allow: admin, super_admin, and built-in Django superusers
        Deny: regular employees (role='employee')
        """
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return True
        
        if hasattr(user, 'role'):
            return user.role in ['admin', 'super_admin']
        
        return False
    

class AdminLogout(View):
    @method_decorator(never_cache)
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('admin-login')

class AdminDashboard(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):

        
        today = date.today()
        current_month = today.month
        current_year = today.year
        first_day_of_month = date(current_year, current_month, 1)
        last_day_of_month = date(current_year, current_month + 1, 1) - timedelta(days=1) if current_month < 12 else date(current_year, 12, 31)
        
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        total_employees = Employee.objects.filter(
            is_superuser=False, 
            is_active=True,
            role='employee'
        ).count()
        
        active_employees = Employee.objects.filter(
            is_superuser=False,
            is_active=True,
            role='employee'
        ).count()
        
        inactive_employees = Employee.objects.filter(
            is_superuser=False,
            is_active=False
        ).count()
        
        # 2. Attendance Statistics (Today) - FIXED QUERY
        today_attendance = AttendanceCheck.objects.filter(
            check_date=today,
            employee__is_superuser=False,
            employee__role='employee'
        )
        
        check_in_count = today_attendance.filter(check_type='in').count()
        check_out_count = today_attendance.filter(check_type='out').count()
        
        # Employees present today (at least checked in once) - FIXED QUERY
        employees_present_ids = AttendanceCheck.objects.filter(
            check_date=today,
            check_type='in',
            employee__is_superuser=False,
            employee__is_active=True,
            employee__role='employee'
        ).values_list('employee_id', flat=True).distinct()
        
        employees_present = len(set(employees_present_ids))
        
        # 3. Leave Statistics
        pending_leaves = Leave.objects.filter(status='pending').count()
        approved_leaves_month = Leave.objects.filter(
            status='approved',
            start_date__month=current_month,
            start_date__year=current_year
        ).count()
        
        # Active leaves today (approved and within date range)
        active_leaves_today = Leave.objects.filter(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        # 4. Task Statistics
        total_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee'
        ).count()
        
        completed_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee',
            status='completed'
        ).count()
        
        in_progress_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee',
            status='in_progress'
        ).count()
        
        # Urgent tasks (due today or overdue)
        urgent_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee',
            due_date__date__lte=today
        ).exclude(status='completed').count()
        
        # 5. Today's Task Distribution
        today_tasks_by_type = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee',
            task_assign_time__date=today
        ).values('task_type').annotate(count=Count('id'))
        
        # 6. Attendance Rate (This Week) - FIXED QUERY
        week_attendance = {}
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            # Get distinct employee IDs who checked in on this day
            day_employee_ids = AttendanceCheck.objects.filter(
                check_date=day,
                employee__is_superuser=False,
                employee__role='employee',
                check_type='in'
            ).values_list('employee_id', flat=True).distinct()
            
            week_attendance[day.strftime('%a')] = len(set(day_employee_ids))
        
        # 7. Monthly Leave Trend (Last 6 months)
        monthly_leaves = []
        for i in range(5, -1, -1):  # Last 6 months
            month_date = today - timedelta(days=30*i)
            month_start = date(month_date.year, month_date.month, 1)
            month_end = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1) if month_date.month < 12 else date(month_date.year, 12, 31)
            
            leaves_count = Leave.objects.filter(
                status='approved',
                start_date__gte=month_start,
                start_date__lte=month_end
            ).count()
            
            monthly_leaves.append({
                'month': month_start.strftime('%b'),
                'count': leaves_count
            })
        
        # 8. Top Performing Employees (by completed tasks)
        top_employees = Employee.objects.filter(
            is_superuser=False,
            is_active=True,
            role='employee'
        ).annotate(
            task_count=Count('tasks', filter=Q(tasks__status='completed'))
        ).order_by('-task_count')[:5]
        
        # 9. Recent Activities
        recent_leaves = Leave.objects.filter(
            status='pending'
        ).select_related('employee').order_by('-created_at')[:5]
        
        recent_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee'
        ).select_related('employee').order_by('-created_at')[:5]
        
        recent_attendance = AttendanceCheck.objects.filter(
            employee__is_superuser=False,
            employee__role='employee'
        ).select_related('employee').order_by('-created_at')[:5]
        
        # 10. Task Completion Rate
        if total_tasks > 0:
            task_completion_rate = round((completed_tasks / total_tasks) * 100, 1)
        else:
            task_completion_rate = 0
        
        # 11. Attendance Percentage (Today)
        attendance_percentage = round((employees_present / active_employees * 100), 1) if active_employees > 0 else 0
        
        # 12. Break Statistics (Today)
        today_breaks = BreakTimer.objects.filter(
            date=today,
            employee__is_superuser=False,
            employee__role='employee'
        ).count()
        
        # 13. Get task counts for Not Started (calculate it)
        not_started_tasks = Task.objects.filter(
            employee__is_superuser=False,
            employee__role='employee',
            status='not_started'
        ).count()
        
        context = {
            # Employee Statistics
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            
            # Attendance Statistics
            'check_in_count': check_in_count,
            'check_out_count': check_out_count,
            'employees_present': employees_present,
            'attendance_percentage': attendance_percentage,
            'today_breaks': today_breaks,
            
            # Leave Statistics
            'pending_leaves': pending_leaves,
            'approved_leaves_month': approved_leaves_month,
            'active_leaves_today': active_leaves_today,
            
            # Task Statistics
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'urgent_tasks': urgent_tasks,
            'not_started_tasks': not_started_tasks,
            'task_completion_rate': task_completion_rate,
            
            # Today's Distribution
            'today_tasks_by_type': today_tasks_by_type,
            
            # Weekly Data
            'week_attendance': week_attendance,
            
            # Monthly Trends
            'monthly_leaves': monthly_leaves,
            
            # Top Performers
            'top_employees': top_employees,
            
            # Recent Activities
            'recent_leaves': recent_leaves,
            'recent_tasks': recent_tasks,
            'recent_attendance': recent_attendance,
            
            # Dates for display
            'today': today.strftime('%B %d, %Y'),
            'current_month': today.strftime('%B %Y'),
            'first_day_of_month': first_day_of_month.strftime('%b %d'),
            'last_day_of_month': last_day_of_month.strftime('%b %d'),
        }
        
        return render(request, 'dashboard.html', context)
    

class EmployeeManage(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):
        employees = Employee.objects.filter(
            role='employee',  
            is_superuser=False  
        ).order_by('-id')
        
        context = {
            'employees': employees
        }
        return render(request, 'customer.html', context)
    

class EmployeeCreate(LoginRequiredMixin, View):
    login_url = '/admin-login/'

    def get(self, request):
        context = {
            'role_choices': Employee.ROLE_CHOICES,
            'employee_type_choices': Employee.EMPLOYEE_TYPE_CHOICES,
            'designation_choices': Employee.DESIGNATION_CHOICES,
            'department_choices': Employee.DEPARTMENT_CHOICES,
            'profession_choices': Employee.PROFESSION,
            'relation_choices': Employee.RELATION_CHOICES,
            'document_choices': VisaDetails.DOCUMENT_TYPES,
        }
        return render(request, 'create_customer.html', context)

    def post(self, request):
        try: 
            employee_id = request.POST.get('employeeId', '').strip()
            
            if not employee_id:
                messages.error(request, 'Employee ID is required!')
                return self.get(request)
            
            if Employee.objects.filter(employeeId=employee_id).exists():
                messages.error(request, f'Employee with ID {employee_id} already exists.')
                return self.get(request)
            
            employee = Employee(
                employeeId=employee_id,
                employee_name=request.POST.get('employee_name', ''),
                role=request.POST.get('role', 'employee'),
                employee_type=request.POST.get('employee_type', 'service'),
                designation=request.POST.get('designation', 'car_service_associate'),
                department=request.POST.get('department', 'service'),
                profession=request.POST.get('profession', 'field_service_specialist'),
                branch_location=request.POST.get('branch_location', ''),
                company_name=request.POST.get('company_name', 'Your Company Name'),
                reporting_manager=request.POST.get('reporting_manager', ''),
                mobile_number=request.POST.get('mobile_number', ''),
                email=request.POST.get('email', ''),
                home_address=request.POST.get('home_address', ''),
                nationality=request.POST.get('nationality', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_number=request.POST.get('emergency_contact_number', ''),
                emergency_contact_relation=request.POST.get('emergency_contact_relation', ''),
                is_active=request.POST.get('is_active') == 'true'
            )
            
            date_of_joining = request.POST.get('date_of_joining')
            date_of_birth = request.POST.get('date_of_birth')
            
            if date_of_joining:
                employee.date_of_joining = date_of_joining
            if date_of_birth:
                employee.date_of_birth = date_of_birth
            
            if 'profile_pic' in request.FILES:
                employee.profile_pic = request.FILES['profile_pic']
            
            password = request.POST.get('password', '').strip()
            if password:
                employee.set_password(password)
            else:
                employee.set_password('default123')
            
            employee.save()
            print(f"Employee saved: {employee.employeeId}")  
            print(request.POST.get('emirates_id_number'),"what i do")

            visa_details = VisaDetails(
                employee=employee,
                visa_number=request.POST.get('visa_number', ''),
                visa_expiry_date=request.POST.get('visa_expiry_date') or None,
                passport_number=request.POST.get('passport_number', ''),
                passport_expiry_date=request.POST.get('passport_expiry_date') or None,
                emirates_id_number=request.POST.get('emirates_id_number', ''),
                emirates_id_expiry=request.POST.get('emirates_id_expiry') or None,
            )
            visa_details.save()
            print("Visa details saved")  
            
            # Handle document uploads
            document_types = request.POST.getlist('document_types[]')
            document_files = request.FILES.getlist('document_files[]')
            
            print(f"Document types: {document_types}")  
            print(f"Document files: {[f.name for f in document_files]}")  


            
            for i, (doc_type, doc_file) in enumerate(zip(document_types, document_files)):
                if doc_type and doc_file:
                    try:
                        Document.objects.create(
                            visa_details=visa_details,
                            document_type=doc_type,
                            document_file=doc_file
                        )
                        print(f"Document {i+1} saved: {doc_type}")  
                    except Exception as doc_error:
                        print(f"Error saving document {i+1}: {str(doc_error)}")  
            
            messages.success(request, f'Employee {employee.employeeId} created successfully!')
            return redirect('employee-manage')  # Make sure this URL name exists
            
        except Exception as e:
            print(f"Error in EmployeeCreate: {str(e)}")  
            
            context = {
                'role_choices': Employee.ROLE_CHOICES,
                'employee_type_choices': Employee.EMPLOYEE_TYPE_CHOICES,
                'designation_choices': Employee.DESIGNATION_CHOICES,
                'department_choices': Employee.DEPARTMENT_CHOICES,
                'profession_choices': Employee.PROFESSION,
                'relation_choices': Employee.RELATION_CHOICES,
                'document_choices': VisaDetails.DOCUMENT_TYPES,
            }
            return render(request, 'create_customer.html', context)


class EmployeeDetailView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request, employee_id):
        print(f"Employee ID received: {employee_id}")
        try:
            employee = Employee.objects.select_related('visa_details').prefetch_related('visa_details__documents').get(
                id=employee_id,
                is_superuser=False
            )

            print(f"Employee found: {employee.employeeId}")
            
            context = {
                'employee': employee,
            }
            
            return render(request, 'employee_details.html', context)
            
        except Employee.DoesNotExist:
            print(f"Employee with id {employee_id} does not exist")
            messages.error(request, 'Employee not found')
            return redirect('employee-manage')  
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error loading employee details: {str(e)}')
            return redirect('employee-manage')  
        






class EmployeeEditView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request, employee_id):
        try:
            employee = Employee.objects.select_related('visa_details').prefetch_related('visa_details__documents').get(
                id=employee_id,
                is_superuser=False
            )

            # Get visa details if exists
            visa_details = None
            if hasattr(employee, 'visa_details'):
                visa_details = employee.visa_details


            context = {
                'employee': employee,
                'visa_details': visa_details,
                'role_choices': Employee.ROLE_CHOICES,
                'employee_type_choices': Employee.EMPLOYEE_TYPE_CHOICES,
                'designation_choices': Employee.DESIGNATION_CHOICES,
                'department_choices': Employee.DEPARTMENT_CHOICES,
                'profession_choices': Employee.PROFESSION,
                'relation_choices': Employee.RELATION_CHOICES,
                'document_choices': VisaDetails.DOCUMENT_TYPES,
            }

            return render(request, 'edit_customer.html', context)
            
        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found.')
            return redirect('employee-manage')
        except Exception as e:
            messages.error(request, f'Error loading employee: {str(e)}')
            return redirect('employee-manage')
    
    def post(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id, is_superuser=False)
            
            # Update basic employee information
            employee.employeeId = request.POST.get('employeeId', employee.employeeId)
            employee.employee_name = request.POST.get('employee_name', employee.employee_name)
            employee.role = request.POST.get('role', employee.role)
            employee.employee_type = request.POST.get('employee_type', employee.employee_type)
            employee.designation = request.POST.get('designation', employee.designation)
            employee.department = request.POST.get('department', employee.department)
            employee.profession = request.POST.get('profession', employee.profession)
            employee.branch_location = request.POST.get('branch_location', employee.branch_location)
            employee.company_name = request.POST.get('company_name', employee.company_name)
            employee.reporting_manager = request.POST.get('reporting_manager', employee.reporting_manager)
            employee.mobile_number = request.POST.get('mobile_number', employee.mobile_number)
            employee.email = request.POST.get('email', employee.email)
            employee.home_address = request.POST.get('home_address', employee.home_address)
            employee.nationality = request.POST.get('nationality', employee.nationality)
            employee.emergency_contact_name = request.POST.get('emergency_contact_name', employee.emergency_contact_name)
            employee.emergency_contact_number = request.POST.get('emergency_contact_number', employee.emergency_contact_number)
            employee.emergency_contact_relation = request.POST.get('emergency_contact_relation', employee.emergency_contact_relation)
            employee.is_active = request.POST.get('is_active') == 'true'
            
            # Handle dates
            date_of_joining = request.POST.get('date_of_joining')
            date_of_birth = request.POST.get('date_of_birth')
            
            if date_of_joining:
                employee.date_of_joining = date_of_joining
            if date_of_birth:
                employee.date_of_birth = date_of_birth
            
            # Handle profile picture
            if 'profile_pic' in request.FILES:
                employee.profile_pic = request.FILES['profile_pic']
            
            employee.save()
            
            # Update or create visa details
            visa_details, created = VisaDetails.objects.get_or_create(employee=employee)
            visa_details.visa_number = request.POST.get('visa_number', visa_details.visa_number)
            visa_details.passport_number = request.POST.get('passport_number', visa_details.passport_number)
            visa_details.emirates_id_number = request.POST.get('emirates_id_number', visa_details.emirates_id_number)
            
            # Handle visa expiry dates
            visa_expiry_date = request.POST.get('visa_expiry_date')
            passport_expiry_date = request.POST.get('passport_expiry_date')
            emirates_id_expiry = request.POST.get('emirates_id_expiry')
            
            if visa_expiry_date:
                visa_details.visa_expiry_date = visa_expiry_date
            if passport_expiry_date:
                visa_details.passport_expiry_date = passport_expiry_date
            if emirates_id_expiry:
                visa_details.emirates_id_expiry = emirates_id_expiry
            
            visa_details.save()
            
            # Handle document uploads
            document_types = request.POST.getlist('document_types[]')
            document_files = request.FILES.getlist('document_files[]')
            
            # Process new documents
            for i, (doc_type, doc_file) in enumerate(zip(document_types, document_files)):
                if doc_type and doc_file:
                    Document.objects.create(
                        visa_details=visa_details,
                        document_type=doc_type,
                        document_file=doc_file
                    )
            
            messages.success(request, f'Employee {employee.employeeId} updated successfully!')
            return redirect('employee-manage')
            
        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found.')
            return redirect('employee-manage')
        except Exception as e:
            messages.error(request, f'Error updating employee: {str(e)}')
            return self.get(request, employee_id)
        


# Create your models here.
class ForgotPasswordView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def post(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id, is_superuser=False)
            
            # Generate a random password
            import string
            import random
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            # Set the new password
            employee.set_password(new_password)
            employee.save()
            
            # Send email with new password (if email is configured)
            if employee.email:
                try:
                    send_mail(
                        'Password Reset - Your Account',
                        f'Hello {employee.employee_name or employee.employeeId},\n\n'
                        f'Your password has been reset. Your new password is: {new_password}\n\n'
                        f'Please login and change your password immediately.\n\n'
                        f'Best regards,\nYour Company',
                        settings.DEFAULT_FROM_EMAIL,
                        [employee.email],
                        fail_silently=True,
                    )
                    messages.success(request, f'Password reset successfully! New password has been sent to {employee.email}.')
                except Exception as e:
                    messages.warning(request, f'Password reset successfully to: {new_password} but email could not be sent.')
            else:
                messages.success(request, f'Password reset successfully! New password: {new_password}')
            
            return JsonResponse({'success': True, 'new_password': new_password})
            
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Employee not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)        
        



class EmployeeDeleteView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def delete(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id, is_superuser=False)
            
            # Store employee info for success message
            employee_id_str = employee.employeeId
            employee_name = employee.employee_name
            
            # Delete the employee
            employee.delete()
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': f'Employee {employee_name} ({employee_id_str}) has been deleted successfully.'
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employee not found.'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error deleting employee: {str(e)}'
            }, status=500)




class CompanyAnnouncementListView(LoginRequiredMixin, ListView):
    login_url = '/admin-login/'
    model = CompanyAnnouncement
    template_name = 'company_announcements.html'
    context_object_name = 'announcements'
    
    def get_queryset(self):
        return CompanyAnnouncement.objects.filter(is_active=True)

class CompanyAnnouncementCreateView(LoginRequiredMixin, CreateView):
    login_url = '/admin-login/'
    model = CompanyAnnouncement
    template_name = 'create_announcement_modal.html'
    fields = ['heading', 'description', 'date', 'is_active']
    success_url = reverse_lazy('company-announcements-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Announcement created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class CompanyAnnouncementDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/admin-login/'
    model = CompanyAnnouncement
    success_url = reverse_lazy('company-announcements-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Announcement deleted successfully!')
        return super().delete(request, *args, **kwargs)
    



class AttendanceListView(LoginRequiredMixin,View):
    def get(self, request):
        # Only include attendance records for employees (exclude superusers and admins)
        queryset = AttendanceCheck.objects.select_related('employee').filter(
            employee__is_superuser=False,
            employee__is_staff=False
        )
        
        # Filter by date
        date_filter = request.GET.get('date')
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(check_date=filter_date)
            except ValueError:
                pass
        
        # Filter by employee
        employee_filter = request.GET.get('employee')
        if employee_filter:
            queryset = queryset.filter(
                Q(employee__employeeId__icontains=employee_filter) |
                Q(employee__employee_name__icontains=employee_filter)
            )
        
        # Filter by check type
        check_type = request.GET.get('check_type')
        if check_type in ['in', 'out']:
            queryset = queryset.filter(check_type=check_type)
        
        # Order to group by employee and show check-in first, then check-out
        attendance_records = queryset.order_by('employee__employeeId', 'check_date', 'check_type')
        
        # Group records by employee and date for template context
        grouped_records = {} 
        for record in attendance_records:
            key = f"{record.employee.employeeId}_{record.check_date}"
            if key not in grouped_records:
                grouped_records[key] = {'employee': record.employee, 'date': record.check_date, 'records': []}
            grouped_records[key]['records'].append(record)
        
        # Convert to list for pagination
        grouped_list = list(grouped_records.values())
        
        paginator = Paginator(grouped_list, 10)  # Show 10 employees per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get filter values
        current_date = request.GET.get('date', '')
        current_employee = request.GET.get('employee', '')
        current_check_type = request.GET.get('check_type', '')
        
        # Get only employees for filter dropdown (exclude superusers and admins)
        employees = Employee.objects.filter(
            is_active=True, 
            is_superuser=False,
            is_staff=False
        )
        
        # Get today's date for default filter
        if not current_date:
            current_date = timezone.now().date().isoformat()
        
        context = {
            'grouped_records': page_obj,
            'page_obj': page_obj,
            'current_date': current_date,
            'current_employee': current_employee,
            'current_check_type': current_check_type,
            'employees': employees,
        }
        
        return render(request, 'attendance_list.html', context)
    



class EmployeeAttendanceDetailView(LoginRequiredMixin,View):
    def get(self, request, pk):
        # Only allow access to employee records, not superusers or admins
        employee = get_object_or_404(
            Employee, 
            id=pk, 
            is_superuser=False,
            is_staff=False
        )
        
        # Get date filter
        date_filter = request.GET.get('date')
        if date_filter:
            try:
                target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()
        
        # Get attendance records for the selected date
        attendance_records = AttendanceCheck.objects.filter(
            employee=employee,
            check_date=target_date
        ).order_by('check_time')
        
        # Get break records for the selected date
        break_records = BreakTimer.objects.filter(
            employee=employee,
            date=target_date
        ).order_by('break_start_time')
        
        # Calculate total break time
        total_break_minutes = 0
        for break_record in break_records:
            if break_record.break_end_time:
                try:
                    start_time = datetime.strptime(break_record.break_start_time, '%H:%M:%S')
                    end_time = datetime.strptime(break_record.break_end_time, '%H:%M:%S')
                    break_duration = (end_time - start_time).total_seconds() / 60
                    total_break_minutes += break_duration
                except ValueError:
                    pass
        
        total_break_time = f"{int(total_break_minutes // 60)}h {int(total_break_minutes % 60)}m"
        
        # Get check-in and check-out times
        check_in = attendance_records.filter(check_type='in').first()
        check_out = attendance_records.filter(check_type='out').last()
        
        # Calculate working hours
        if check_in and check_out:
            try:
                in_time = datetime.strptime(check_in.check_time, '%H:%M:%S')
                out_time = datetime.strptime(check_out.check_time, '%H:%M:%S')
                working_minutes = (out_time - in_time).total_seconds() / 60 - total_break_minutes
                working_hours = f"{int(working_minutes // 60)}h {int(working_minutes % 60)}m"
            except ValueError:
                working_hours = "N/A"
        else:
            working_hours = "N/A"
        
        context = {
            'employee': employee,
            'selected_date': target_date,
            'attendance_records': attendance_records,
            'break_records': break_records,
            'total_break_time': total_break_time,
            'check_in': check_in,
            'check_out': check_out,
            'working_hours': working_hours,
        }
        
        return render(request, 'employee_attendance_detail.html', context)

class DailyAttendanceView(LoginRequiredMixin,View):
    def get(self, request):
        # Get date filter
        date_filter = request.GET.get('date')
        if date_filter:
            try:
                target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()
        
        employees = Employee.objects.filter(
            is_active=True, 
            is_superuser=False,
            is_staff=False
        ).exclude(
            role__in=['super_admin', 'admin']  # Exclude admin roles
        )
                
        # Get attendance data for each employee for the selected date
        daily_data = []
        present_count = 0
        absent_count = 0
        
        for employee in employees:
            attendance_records = AttendanceCheck.objects.filter(
                employee=employee,
                check_date=target_date
            ).order_by('check_time')
            
            break_records = BreakTimer.objects.filter(
                employee=employee,
                date=target_date
            )
            
            check_in = attendance_records.filter(check_type='in').first()
            check_out = attendance_records.filter(check_type='out').last()
            
            # Count present/absent
            if check_in:
                present_count += 1
            else:
                absent_count += 1
            
            # Calculate total break time
            total_break_minutes = 0
            for break_record in break_records:
                if break_record.break_end_time:
                    try:
                        start_time = datetime.strptime(break_record.break_start_time, '%H:%M:%S')
                        end_time = datetime.strptime(break_record.break_end_time, '%H:%M:%S')
                        break_duration = (end_time - start_time).total_seconds() / 60
                        total_break_minutes += break_duration
                    except ValueError:
                        pass
            
            # Calculate working hours
            working_hours = "N/A"
            if check_in and check_out:
                try:
                    in_time = datetime.strptime(check_in.check_time, '%H:%M:%S')
                    out_time = datetime.strptime(check_out.check_time, '%H:%M:%S')
                    working_minutes = (out_time - in_time).total_seconds() / 60 - total_break_minutes
                    working_hours = f"{int(working_minutes // 60)}h {int(working_minutes % 60)}m"
                except ValueError:
                    working_hours = "N/A"
            
            daily_data.append({
                'employee': employee,
                'check_in': check_in,
                'check_out': check_out,
                'break_count': break_records.count(),
                'total_break_time': f"{int(total_break_minutes // 60)}h {int(total_break_minutes % 60)}m",
                'working_hours': working_hours,
                'status': 'Present' if check_in else 'Absent'
            })
        
        context = {
            'selected_date': target_date,
            'daily_data': daily_data,
            'total_employees': len(daily_data),
            'present_count': present_count,
            'absent_count': absent_count,
        }
        
        return render(request, 'daily_attendance.html', context)
    




class TaskDashboardView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):
        # Get filter parameters
        date_filter = request.GET.get('date')
        employee_filter = request.GET.get('employee')
        status_filter = request.GET.get('status')
        task_type_filter = request.GET.get('task_type')
        
        # Base queryset
        tasks = Task.objects.select_related('employee').filter(
            employee__is_superuser=False,
            employee__is_staff=False
        )
        
        # Apply filters
        if date_filter:
            try:
                target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                tasks = tasks.filter(
                    Q(task_assign_time__date=target_date) |
                    Q(task_start_time__date=target_date) |
                    Q(task_completed_date__date=target_date) |
                    Q(due_date__date=target_date)
                )
            except ValueError:
                pass
        
        if employee_filter:
            tasks = tasks.filter(
                Q(employee__employeeId__icontains=employee_filter) |
                Q(employee__employee_name__icontains=employee_filter)
            )
        
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        
        if task_type_filter:
            tasks = tasks.filter(task_type=task_type_filter)
        
        # Statistics
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        in_progress_tasks = tasks.filter(status='in_progress').count()
        not_started_tasks = tasks.filter(status='not_started').count()
        
        # Tasks by type
        tasks_by_type = tasks.values('task_type').annotate(count=Count('id'))
        
        # Today's tasks
        today = timezone.now().date()
        todays_tasks = tasks.filter(
            Q(task_assign_time__date=today) |
            Q(due_date__date=today)
        ).order_by('priority', 'due_date')
        
        # Urgent tasks (due today or overdue)
        urgent_tasks = tasks.filter(
            Q(due_date__date=today) |
            Q(due_date__lt=timezone.now())
        ).exclude(status='completed').order_by('due_date')
        
        context = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'not_started_tasks': not_started_tasks,
            'tasks_by_type': tasks_by_type,
            'todays_tasks': todays_tasks,
            'urgent_tasks': urgent_tasks,
            'current_date': date_filter or today.isoformat(),
            'current_employee': employee_filter or '',
            'current_status': status_filter or '',
            'current_task_type': task_type_filter or '',
            'employees': Employee.objects.filter(is_active=True, is_superuser=False, is_staff=False),
            'status_choices': Task.TASK_STATUS_CHOICES,
            'task_type_choices': Task.TASK_TYPE_CHOICES,
        }
        
        return render(request, 'task_dashboard.html', context)

class TaskListView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):
        # Get filter parameters
        date_filter = request.GET.get('date')
        employee_filter = request.GET.get('employee')
        status_filter = request.GET.get('status')
        task_type_filter = request.GET.get('task_type')
        priority_filter = request.GET.get('priority')
        
        # Base queryset
        tasks = Task.objects.select_related('employee').prefetch_related(
            'delivery_details', 'office_details', 'service_tasks'
        ).filter(
            employee__is_superuser=False,
            employee__is_staff=False
        )
        
        # Apply filters
        if date_filter:
            try:
                target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                tasks = tasks.filter(
                    Q(task_assign_time__date=target_date) |
                    Q(task_start_time__date=target_date) |
                    Q(task_completed_date__date=target_date) |
                    Q(due_date__date=target_date)
                )
            except ValueError:
                pass
        
        if employee_filter:
            tasks = tasks.filter(
                Q(employee__employeeId__icontains=employee_filter) |
                Q(employee__employee_name__icontains=employee_filter)
            )
        
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        
        if task_type_filter:
            tasks = tasks.filter(task_type=task_type_filter)
            
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)
        
        # Order by priority and due date
        tasks = tasks.order_by('-priority', 'due_date', '-created_at')
        
        # Pagination
        paginator = Paginator(tasks, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'tasks': page_obj,
            'page_obj': page_obj,
            'current_date': date_filter or '',
            'current_employee': employee_filter or '',
            'current_status': status_filter or '',
            'current_task_type': task_type_filter or '',
            'current_priority': priority_filter or '',
            'employees': Employee.objects.filter(is_active=True, is_superuser=False, is_staff=False),
            'status_choices': Task.TASK_STATUS_CHOICES,
            'task_type_choices': Task.TASK_TYPE_CHOICES,
            'priority_choices': Task.PRIORITY_CHOICES,
        }
        
        return render(request, 'task_list.html', context)

class TaskDetailView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request, task_id):
        try:
            task = Task.objects.select_related(
                'employee', 
                'delivery_details', 
                'office_details'
            ).prefetch_related(
                'service_tasks',
                'task_duties__duty',
                'progress_images'
            ).get(
                id=task_id,
                employee__is_superuser=False,
                employee__is_staff=False
            )
            
            context = {
                'task': task,
            }
            
            return render(request, 'task_detail.html', context)
            
        except Task.DoesNotExist:
            messages.error(request, 'Task not found')
            return redirect('task-list')

class CreateTaskView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):
        context = {
            'employees': Employee.objects.filter(is_active=True, is_superuser=False, is_staff=False),
            'task_type_choices': Task.TASK_TYPE_CHOICES,
            'priority_choices': Task.PRIORITY_CHOICES,
            'status_choices': Task.TASK_STATUS_CHOICES,
            'service_type_choices': ServiceTask.SERVICE_TYPE_CHOICES,
            'office_task_choices': OfficeTask.OFFICE_TASK_TYPE_CHOICES,
        }
        return render(request, 'create_task.html', context)
    
    def post(self, request):
        try:
            # Create main task
            task = Task(
                employee_id=request.POST.get('employee'),
                task_type=request.POST.get('task_type'),
                heading=request.POST.get('heading'),
                status=request.POST.get('status', 'not_started'),
                address=request.POST.get('address'),
                description=request.POST.get('description'),
                customer_name=request.POST.get('customer_name'),
                task_notes=request.POST.get('task_notes'),
                priority=request.POST.get('priority', 'medium'),
                location=request.POST.get('location'),
                percentage_completed=int(request.POST.get('percentage_completed', 0)),
                vehicle_details=request.POST.get('vehicle_details'),
                vehicle_model=request.POST.get('vehicle_model'),
                vehicle_year=request.POST.get('vehicle_year'),
                vehicle_color=request.POST.get('vehicle_color'),
            )
            
            # Handle dates
            task_assign_time = request.POST.get('task_assign_time')
            task_start_time = request.POST.get('task_start_time')
            task_completed_date = request.POST.get('task_completed_date')
            due_date = request.POST.get('due_date')
            
            if task_assign_time:
                task.task_assign_time = datetime.fromisoformat(task_assign_time)
            if task_start_time:
                task.task_start_time = datetime.fromisoformat(task_start_time)
            if task_completed_date:
                task.task_completed_date = datetime.fromisoformat(task_completed_date)
            if due_date:
                task.due_date = datetime.fromisoformat(due_date)
            
            # Handle vehicle images
            if 'vehicle_image_before' in request.FILES:
                task.vehicle_image_before = request.FILES['vehicle_image_before']
            if 'vehicle_image_after' in request.FILES:
                task.vehicle_image_after = request.FILES['vehicle_image_after']
            
            task.save()
            
            # Create specific task type details
            task_type = request.POST.get('task_type')
            
            if task_type == 'delivery':
                DeliveryTask.objects.create(
                    task=task,
                    invoice_numbers=request.POST.get('invoice_numbers', ''),
                    delivery_location=request.POST.get('delivery_location', '')
                )
            elif task_type == 'office':
                OfficeTask.objects.create(
                    task=task,
                    office_task_type=request.POST.get('office_task_type'),
                    specific_date=request.POST.get('specific_date') or None,
                    employee_profiles_to_review=request.POST.get('employee_profiles_to_review', '')
                )
            elif task_type == 'service':
                ServiceTask.objects.create(
                    task=task,
                    service_type=request.POST.get('service_type'),
                    vin_number=request.POST.get('vin_number', ''),
                    work_location=request.POST.get('work_location', ''),
                    shared_staff_details=request.POST.get('shared_staff_details', '')
                )
            
            messages.success(request, f'Task "{task.heading}" created successfully!')
            return redirect('task-detail', task_id=task.id)
            
        except Exception as e:
            messages.error(request, f'Error creating task: {str(e)}')
            return self.get(request)    
        




class LeaveListView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request):
        # Get filter parameters from request
        from_date = request.GET.get('from_date', '')
        to_date = request.GET.get('to_date', '')
        employee_id = request.GET.get('employee', '')
        status = request.GET.get('status', '')
        category = request.GET.get('category', '')
        
        # Get current month for monthly leave count
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Base queryset - different for admin vs regular employees
        if request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin']:
            leaves = Leave.objects.all().select_related('employee', 'approved_by')
            
            # Calculate monthly leave counts for all employees
            employees_monthly_leaves = {}
            for emp in Employee.objects.filter(is_superuser=False, is_active=True):
                monthly_count = Leave.objects.filter(
                    employee=emp,
                    start_date__month=current_month,
                    start_date__year=current_year,
                    status='approved'
                ).count()
                employees_monthly_leaves[emp.employeeId] = monthly_count
        else:
            # Regular employees can only see their own leaves
            leaves = Leave.objects.filter(employee=request.user).select_related('employee', 'approved_by')
            
            # Calculate monthly leave count for current user
            monthly_count = Leave.objects.filter(
                employee=request.user,
                start_date__month=current_month,
                start_date__year=current_year,
                status='approved'
            ).count()
            employees_monthly_leaves = {request.user.employeeId: monthly_count}
        
        # Apply filters if provided
        if from_date:
            leaves = leaves.filter(start_date__gte=from_date)
        if to_date:
            leaves = leaves.filter(end_date__lte=to_date)
        if employee_id:
            leaves = leaves.filter(employee__employeeId=employee_id)
        if status:
            leaves = leaves.filter(status=status)
        if category:
            leaves = leaves.filter(category=category)
        
        # Order by latest first
        leaves = leaves.order_by('-created_at')
        
        # Get statistics counts
        total_leaves = leaves.count()
        pending_count = leaves.filter(status='pending').count()
        approved_count = leaves.filter(status='approved').count()
        rejected_count = leaves.filter(status='rejected').count()
        cancelled_count = leaves.filter(status='cancelled').count()
        
        # Count active leaves (approved and currently within date range)
        today = date.today()
        active_count = leaves.filter(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        # Count upcoming leaves (approved and start date in future)
        upcoming_count = leaves.filter(
            status='approved',
            start_date__gt=today
        ).count()
        
        # Get all employees for filter dropdown
        if request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin']:
            employees = Employee.objects.filter(
                is_superuser=False,
                is_active=True
            ).order_by('employee_name')
        else:
            # Regular employees can only see themselves in the dropdown
            employees = Employee.objects.filter(id=request.user.id)
        
        # Prepare context
        context = {
            'leaves': leaves,
            'employees': employees,
            'status_choices': Leave.STATUS_CHOICES,
            'category_choices': Leave.LEAVE_CATEGORY_CHOICES,
            'ticket_eligibility_choices': Leave.TICKET_ELIGIBILITY_CHOICES,
            
            # Filter values for form preservation
            'selected_employee': employee_id,
            'selected_status': status,
            'selected_category': category,
            'from_date': from_date,
            'to_date': to_date,
            
            # Statistics
            'total_leaves': total_leaves,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'cancelled_count': cancelled_count,
            'active_count': active_count,
            'upcoming_count': upcoming_count,
            
            # Monthly leave counts
            'employees_monthly_leaves': employees_monthly_leaves,
            'current_month': current_month,
            'current_year': current_year,
            
            # User info for template
            'is_admin': request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin'],
            'is_employee': request.user.role == 'employee',
        }
        
        return render(request, 'leave_list.html', context)


class LeaveDetailView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def get(self, request, pk):
        try:
            leave = Leave.objects.select_related('employee', 'approved_by').get(pk=pk)
            
            # Check permission
            if not (request.user.is_staff or 
                    request.user.is_superuser or 
                    request.user.role in ['super_admin', 'admin'] or 
                    leave.employee == request.user):
                return redirect('leave-list')
            
            # Calculate monthly leave count for this employee
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            monthly_leave_count = Leave.objects.filter(
                employee=leave.employee,
                start_date__month=current_month,
                start_date__year=current_year,
                status='approved'
            ).count()
            
            context = {
                'leave': leave,
                'monthly_leave_count': monthly_leave_count,
                'current_month': current_month,
                'current_year': current_year,
                'is_admin': request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin'],
            }
            return render(request, 'leave_detail.html', context)
            
        except Leave.DoesNotExist:
            messages.error(request, 'Leave not found.')
            return redirect('leave-list')


class ApproveLeaveView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def post(self, request, pk):
        # Only admins can approve leaves
        if not (request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin']):
            messages.error(request, 'Permission denied.')
            return redirect('leave-detail', pk=pk)
        
        try:
            leave = Leave.objects.get(pk=pk)
            
            if leave.status != 'pending':
                messages.error(request, 'Leave is not in pending status.')
                return redirect('leave-detail', pk=pk)
            
            leave.status = 'approved'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            
            messages.success(request, 'Leave approved successfully.')
            return redirect('leave-detail', pk=pk)
            
        except Leave.DoesNotExist:
            messages.error(request, 'Leave not found.')
            return redirect('leave-list')
        except Exception as e:
            messages.error(request, f'Error approving leave: {str(e)}')
            return redirect('leave-detail', pk=pk)


class RejectLeaveView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def post(self, request, pk):
        # Only admins can reject leaves
        if not (request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin']):
            messages.error(request, 'Permission denied.')
            return redirect('leave-detail', pk=pk)
        
        try:
            leave = Leave.objects.get(pk=pk)
            
            if leave.status != 'pending':
                messages.error(request, 'Leave is not in pending status.')
                return redirect('leave-detail', pk=pk)
            
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('leave-detail', pk=pk)
            
            leave.status = 'rejected'
            leave.rejection_reason = rejection_reason
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            
            messages.success(request, 'Leave rejected successfully.')
            return redirect('leave-detail', pk=pk)
            
        except Leave.DoesNotExist:
            messages.error(request, 'Leave not found.')
            return redirect('leave-list')
        except Exception as e:
            messages.error(request, f'Error rejecting leave: {str(e)}')
            return redirect('leave-detail', pk=pk)


class CancelLeaveView(LoginRequiredMixin, View):
    login_url = '/admin-login/'
    
    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
            
            # Only the employee can cancel their own leave
            if leave.employee != request.user:
                messages.error(request, 'You can only cancel your own leaves.')
                return redirect('leave-detail', pk=pk)
            
            if leave.status != 'pending':
                messages.error(request, 'Only pending leaves can be cancelled.')
                return redirect('leave-detail', pk=pk)
            
            leave.status = 'cancelled'
            leave.save()
            
            messages.success(request, 'Leave cancelled successfully.')
            return redirect('leave-detail', pk=pk)
            
        except Leave.DoesNotExist:
            messages.error(request, 'Leave not found.')
            return redirect('leave-list')
        except Exception as e:
            messages.error(request, f'Error cancelling leave: {str(e)}')
            return redirect('leave-detail', pk=pk)