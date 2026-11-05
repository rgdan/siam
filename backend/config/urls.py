
from api import views
from api import reports as report_views
from api import consolidated_reports as consolidated_views
from audit.views import AuditList
from django.urls import path
from incidents.views import register_incident
from system_configuration import views as configuration_views
from visitors.views import register_entry

from collection_integrity import views as collection_views

urlpatterns = [
    path("api/pieces/<int:piece_id>/reactivate/", collection_views.reactivate, name="piece-reactivate"),
    path("api/pieces/<int:piece_id>/recover/", collection_views.recover, name="piece-recover"),
    path("api/pieces/<int:piece_id>/decommission/", collection_views.decommission, name="piece-decommission"),
    path("api/pieces/<int:piece_id>/missing/", collection_views.missing, name="piece-missing"),
    path("api/pieces/<int:piece_id>/loan/", collection_views.loan, name="piece-loan"),
    path("api/pieces/<int:piece_id>/return/", collection_views.return_loan, name="piece-return"),
    path("api/collection/report/", collection_views.collection_report, name="collection-report"),
    path("api/pieces/", collection_views.pieces, name="pieces"),
    path("api/pieces/<int:piece_id>/", collection_views.piece_detail, name="piece-detail"),
    path("api/pieces/<int:piece_id>/photos/", collection_views.upload_photos, name="piece-photos"),
    path("api/pieces/<int:piece_id>/photos/order/", collection_views.reorder_photos, name="piece-photo-order"),
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
    path("api/events/", views.events, name="events"),
    path("api/events/internal/", views.internal_events, name="internal-events"),

    # SIAM-15: modificación y cancelación de eventos.
    path(
        "api/events/<int:event_id>/",
        views.event_detail,
        name="event-detail",
    ),
    path(
        "api/events/<int:event_id>/cancel/",
        views.cancel_event,
        name="event-cancel",
    ),

    # SIAM-16: registro de asistencia real.
    path(
        "api/events/<int:event_id>/attendance/",
        views.event_attendance,
        name="event-attendance",
    ),

    # SIAM-17: reporte de asistencia esperada vs. real.
    path(
        "api/reports/attendance/",
        report_views.attendance_report,
        name="attendance-report",
    ),
    # SIAM-27: reportes consolidados del museo.
    path(
        "api/reports/consolidated/",
        consolidated_views.consolidated_report,
        name="consolidated-report",
    ),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.not_found
handler500 = views.server_error
