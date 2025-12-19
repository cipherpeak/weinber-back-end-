from django.utils import timezone
from home.models import Leave, AttendanceCheck
from datetime import datetime

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
            # Try to parse the date strings
            try:
                # If dates are stored in format like "10 November 2025"
                if leave.start_date and leave.end_date:
                    # Method 1: Try to parse common date formats
                    date_formats = [
                        '%d %B %Y',      # "10 November 2025"
                        '%d-%b-%Y',      # "10-Nov-2025"
                        '%Y-%m-%d',      # "2025-11-10"
                        '%d/%m/%Y',      # "10/11/2025"
                        '%m/%d/%Y',      # "11/10/2025"
                        '%B %d, %Y',     # "November 10, 2025"
                    ]
                    
                    start_date_obj = None
                    end_date_obj = None
                    
                    for date_format in date_formats:
                        try:
                            if not start_date_obj:
                                start_date_obj = datetime.strptime(leave.start_date, date_format)
                            if not end_date_obj:
                                end_date_obj = datetime.strptime(leave.end_date, date_format)
                        except:
                            continue
                    
                    if start_date_obj and end_date_obj:
                        date_range = f'{start_date_obj.strftime("%b %d")} - {end_date_obj.strftime("%b %d")}'
                    else:
                        # If parsing fails, use the original strings
                        date_range = f'{leave.start_date} - {leave.end_date}'
                else:
                    date_range = "Date not specified"
                    
            except Exception as e:
                # If any error occurs, use the original strings
                date_range = f'{leave.start_date} - {leave.end_date}'
            
            # Get employee name safely
            employee_name = "Unknown"
            if leave.employee and hasattr(leave.employee, 'employee_name'):
                employee_name = leave.employee.employee_name
            elif leave.employee and hasattr(leave.employee, 'user'):
                employee_name = leave.employee.user.get_full_name() or leave.employee.user.username
            
            leave_notifications.append({
                'id': leave.id,
                'type': 'leave',
                'title': 'New Leave Application',
                'message': f'{employee_name} applied for {leave.get_category_display()} leave',
                'time': leave.created_at,
                'url': f'/leaves/{leave.id}/',
                'icon': 'calendar_month',
                'employee_name': employee_name,
                'leave_type': leave.get_category_display(),
                'days': leave.total_days,
                'date_range': date_range,
                'status': leave.status,
                'category': leave.category,
            })
        
        # Total unread count (just leaves for now)
        total_unread_count = pending_leaves_count
        
        context.update({
            'pending_leaves_count': pending_leaves_count,
            'leave_notifications': leave_notifications,
            'total_notifications_count': total_unread_count,
        })
    
    return context


# Additional helper function for date parsing
def parse_date_string(date_str):
    """
    Helper function to parse date strings from various formats
    """
    if not date_str:
        return None
    
    date_formats = [
        '%d %B %Y',      # "10 November 2025"
        '%d-%b-%Y',      # "10-Nov-2025"
        '%Y-%m-%d',      # "2025-11-10"
        '%d/%m/%Y',      # "10/11/2025"
        '%m/%d/%Y',      # "11/10/2025"
        '%B %d, %Y',     # "November 10, 2025"
        '%d %b %Y',      # "10 Nov 2025"
        '%Y/%m/%d',      # "2025/11/10"
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            continue
    
    # Try to parse with dateutil if available (more flexible)
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except:
        pass
    
    return None