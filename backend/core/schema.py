from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as s

ERRORS = {
    400: OpenApiResponse(OpenApiTypes.OBJECT, description="Invalid input: field errors or detail/non_field_errors."),
    401: OpenApiResponse(description="No active session, or invalid login credentials."),
    403: OpenApiResponse(description="Missing role permission or invalid/missing CSRF token."),
    404: OpenApiResponse(description="Resource or page not found."),
}

DATE_FILTERS = [
    OpenApiParameter("fecha_inicio", OpenApiTypes.DATE, description="Inclusive start date (YYYY-MM-DD), Costa Rica time."),
    OpenApiParameter("fecha_fin", OpenApiTypes.DATE, description="Inclusive end date (YYYY-MM-DD), Costa Rica time."),
]

CONFIRM = inline_serializer("Confirmation", {"confirm": s.BooleanField(help_text="Must be true.")})

DETAIL = inline_serializer("Detail", {"detail": s.CharField()})

HEALTH = inline_serializer("Health", {"estado": s.CharField(default="ok")})
