from django.urls import path

from api import views


urlpatterns = [path("api/health/", views.health, name="health")]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.not_found
handler500 = views.server_error
