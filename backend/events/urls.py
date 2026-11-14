from django.urls import path
from . import views, reports


urlpatterns = [
    path('events/', views.events, name='events'),
    path('events/internal/', views.internal_events, name='internal-events'),
    path('events/<int:event_id>/', views.event_detail, name='event-detail'),
    path('events/<int:event_id>/cancel/', views.cancel_event, name='event-cancel'),
    path('events/<int:event_id>/attendance/', views.event_attendance, name='event-attendance'),
    path('reports/attendance/', reports.attendance_report, name='attendance-report'),
]
