from django.urls import path
from . import views


urlpatterns = [
    path('configuration/', views.configuration, name='configuration'),
    path('configuration/<str:key>/reset/', views.reset_parameter, name='reset-parameter'),
    path('public/configuration/', views.public_configuration, name='public-configuration'),
]
