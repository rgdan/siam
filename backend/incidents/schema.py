from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS
from .serializers import IncidentSerializer


INCIDENT_PAGE = inline_serializer("IncidentPage", {
    "count": s.IntegerField(), "next": s.URLField(allow_null=True),
    "previous": s.URLField(allow_null=True), "results": IncidentSerializer(many=True),
})

