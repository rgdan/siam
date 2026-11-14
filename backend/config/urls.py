from django.urls import include, path
from core import views


urlpatterns = [
    path("api/", include("core.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("events.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("collection.urls")),
    path("api/", include("incidents.urls")),
    path("api/", include("visitors.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("system_configuration.urls")),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.not_found
handler500 = views.server_error
