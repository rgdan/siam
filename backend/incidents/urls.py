from django.urls import path
from . import views


urlpatterns = [
    path('incidents/', views.register_incident, name='incident-register'),
]
