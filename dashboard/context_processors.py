def user_context(request):
    """
    Context processor to add user-related data to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            # Add employee profile to context if it exists
            if hasattr(request.user, 'employee'):
                context['employee_profile'] = request.user.employee
        except Exception:
            # Handle case where employee profile doesn't exist
            pass
            
    return context


# context_processors.py
from django.utils import timezone
from home.models import Leave, AttendanceCheck

def notifications_context(request):
    if not request.user.is_authenticated:
        return {}
    
    context = {}
    
    # Only for admin users
    if request.user.is_staff or request.user.is_superuser or request.user.role in ['super_admin', 'admin']:
        # Pending leave applications count
        pending_leaves_count = Leave.objects.filter(
            status='pending'
        ).count()
        
        # Get recent pending leaves (last 5)
        recent_pending_leaves = Leave.objects.filter(
            status='pending'
        ).select_related('employee').order_by('-created_at')[:5]
        
        # Format leave notifications
        leave_notifications = []
        for leave in recent_pending_leaves:
            leave_notifications.append({
                'id': leave.id,
                'type': 'leave',
                'title': 'New Leave Application',
                'message': f'{leave.employee.employee_name} applied for {leave.get_category_display()} leave',
                'time': leave.created_at,
                'url': f'/leaves/{leave.id}/',
                'icon': 'calendar_month',
                'employee_name': leave.employee.employee_name,
                'leave_type': leave.get_category_display(),
                'days': leave.total_days,
                'date_range': f'{leave.start_date.strftime("%b %d")} - {leave.end_date.strftime("%b %d")}'
            })
        
        # Total unread count (just leaves for now)
        total_unread_count = pending_leaves_count
        
        context.update({
            'pending_leaves_count': pending_leaves_count,
            'leave_notifications': leave_notifications,
            'total_notifications_count': total_unread_count,
        })
    
    return context