from django.urls import path
from .views import *

urlpatterns = [
    path('', AdminDashboard.as_view(), name='dashboard'),
    path('admin-login/', AdminLogin.as_view(), name='admin-login'),
    path('admin-logout/', AdminLogout.as_view(), name='admin-logout'),
    path('employee-manage/', EmployeeManage.as_view(), name='employee-manage'),
    path('create-employee/', EmployeeCreate.as_view(), name='create-employee'),
    path('employee-details/<int:employee_id>/', EmployeeDetailView.as_view(), name='employee-details'),
    path('edit-employee/<int:employee_id>/', EmployeeEditView.as_view(), name='edit-employee'),
    path('forgot-password/<int:employee_id>/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('delete-employee/<int:employee_id>/', EmployeeDeleteView.as_view(), name='delete-employee'),

    path('company-announcements-list/', CompanyAnnouncementListView.as_view(), name='company-announcements-list'),
    path('company-announcements/create/', CompanyAnnouncementCreateView.as_view(), name='create-announcement'),
    path('company-announcements/<int:pk>/delete/', CompanyAnnouncementDeleteView.as_view(), name='delete-announcement'),


    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/employee/<int:pk>/', EmployeeAttendanceDetailView.as_view(), name='employee-attendance-detail'),
    path('attendance/daily/', DailyAttendanceView.as_view(), name='daily-attendance'),


    path('tasks/dashboard/', TaskDashboardView.as_view(), name='task-dashboard'),
    path('tasks/dashboard-list/', TaskListView.as_view(), name='task-dashboard-list'),
    path('tasks/dashboard/create/', CreateTaskView.as_view(), name='create-dashboard-task'),
    path('tasks/dashboard/<int:task_id>/', TaskDetailView.as_view(), name='task-dashboard-detail'),


    path('leaves/', LeaveListView.as_view(), name='leave-list'),
    path('leaves/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/approve/', ApproveLeaveView.as_view(), name='approve-leave'),
    path('leaves/<int:pk>/reject/', RejectLeaveView.as_view(), name='reject-leave'),
    path('leaves/<int:pk>/cancel/', CancelLeaveView.as_view(), name='cancel-leave'),

]