from django.urls import path
from . import views


urlpatterns = [
    path('visitor-entries/', views.register_entry, name='visitor-entry-register'),
]
