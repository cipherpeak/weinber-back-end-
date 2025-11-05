from django.urls import path
from .views import *

urlpatterns = [
    path('', HomeAPIView.as_view(), name='home-details'),
    path('checkin/', CheckInAPIView.as_view(), name='checkin'),
    path('checkout/', CheckOutAPIView.as_view(), name='checkout'),
    path('break/start/', StartBreakAPIView.as_view(), name='start-break'),
    path('break/end/', EndBreakAPIView.as_view(), name='end-break'),
]
