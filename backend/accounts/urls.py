from django.urls import path
from . import views


urlpatterns = [
    path('auth/csrf/', views.csrf, name='csrf'),
    path('auth/login/', views.sign_in, name='login'),
    path('auth/me/', views.me, name='me'),
    path('auth/logout/', views.sign_out, name='logout'),
    path('users/', views.users, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user-detail'),
]
