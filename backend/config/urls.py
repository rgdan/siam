from django.urls import path

from api import views


urlpatterns = [
    path("api/health/", views.health, name="health"),
    path("api/auth/csrf/", views.csrf, name="csrf"),
    path("api/auth/login/", views.sign_in, name="login"),
    path("api/auth/me/", views.me, name="me"),
    path("api/auth/logout/", views.sign_out, name="logout"),
    path("api/users/", views.users, name="users"),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.not_found
handler500 = views.server_error
