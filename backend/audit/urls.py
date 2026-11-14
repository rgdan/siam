from django.urls import path
from . import views


urlpatterns = [
    path('audit/', views.AuditList.as_view(), name='audit-list'),
]
