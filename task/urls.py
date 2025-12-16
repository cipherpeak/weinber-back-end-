# urls.py
from django.urls import path
from .views import PendingTasksAPIView, SaveTaskProgressAPIView, TaskDetailView, TaskListView,StartTaskAPIView,StartTaskDetailsAPIView,ServiceTaskDAXListView

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:task_id>/start/', StartTaskAPIView.as_view(), name='start-task'),
    path('<int:task_id>/start-details/', StartTaskDetailsAPIView.as_view(), name='start-task-details'),
    path('<int:task_id>/save-progress/', SaveTaskProgressAPIView.as_view(), name='save-task-progress'),
    path('pending/', PendingTasksAPIView.as_view(), name='pending-tasks'),
    path('service-task-dax/', ServiceTaskDAXListView.as_view(), name='service-task-dax'),

]