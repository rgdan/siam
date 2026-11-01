from api import views
from audit.views import AuditList
from django.urls import path
from incidents.views import register_incident
from system_configuration import views as configuration_views
from visitors.views import register_entry

from collection_integrity import views as collection_views

urlpatterns = [
    path("api/pieces/", collection_views.pieces, name="pieces"),
    path("api/pieces/<int:piece_id>/", collection_views.piece_detail, name="piece-detail"),
    path("api/pieces/<int:piece_id>/photos/", collection_views.upload_photos, name="piece-photos"),
    path("api/pieces/<int:piece_id>/photos/order/", collection_views.reorder_photos, name="piece-photo-order"),
    path("api/pieces/<int:piece_id>/photos/<int:photo_id>/", collection_views.delete_photo, name="piece-photo-delete"),
    path("api/incidents/", register_incident, name="incident-register"),
    path("api/visitor-entries/", register_entry, name="visitor-entry-register"),
    path("api/audit/", AuditList.as_view(), name="audit-list"),
    path("api/configuration/", configuration_views.configuration, name="configuration"),
    path("api/configuration/<str:key>/reset/", configuration_views.reset_parameter, name="reset-parameter"),
    path("api/public/configuration/", configuration_views.public_configuration, name="public-configuration"),
    path("api/health/", views.health, name="health"),
    path("api/auth/csrf/", views.csrf, name="csrf"),
    path("api/auth/login/", views.sign_in, name="login"),
    path("api/auth/me/", views.me, name="me"),
    path("api/auth/logout/", views.sign_out, name="logout"),
    path("api/users/", views.users, name="users"),
    path("api/users/<int:user_id>/", views.user_detail, name="user-detail"),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.not_found
handler500 = views.server_error
