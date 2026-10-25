from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission

from .models import AuditEntry


class SystemAdminOnly(BasePermission):
    message = "Acceso exclusivo del administrador de sistema."

    def has_permission(self, request, view):
        user = request.user
        if not (
            user.is_authenticated
            and user.is_active
            and user.role == "administrador_sistema"
        ):
            raise PermissionDenied(self.message)
        return True


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEntry
        fields = [
            "id",
            "user",
            "role",
            "timestamp",
            "action_type",
            "entity",
            "entity_id",
            "changes",
        ]
        read_only_fields = fields


class AuditFilters(serializers.Serializer):
    user = serializers.IntegerField(min_value=1, required=False)
    action_type = serializers.ChoiceField(
        choices=AuditEntry.Action.choices, required=False
    )
    entity = serializers.CharField(max_length=100, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if (
            attrs.get("date_from")
            and attrs.get("date_to")
            and attrs["date_from"] > attrs["date_to"]
        ):
            raise serializers.ValidationError(
                {"date_to": "Debe ser posterior o igual a date_from."}
            )
        return attrs


class AuditPagination(PageNumberPagination):
    page_size = 50


class AuditList(ListAPIView):
    permission_classes = [SystemAdminOnly]
    serializer_class = AuditSerializer
    pagination_class = AuditPagination

    def get_queryset(self):
        filters = AuditFilters(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        lookup = {
            "user": "user_id",
            "action_type": "action_type",
            "entity": "entity",
            "date_from": "timestamp__date__gte",
            "date_to": "timestamp__date__lte",
        }
        return AuditEntry.objects.filter(
            **{lookup[k]: v for k, v in filters.validated_data.items()}
        )

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response
