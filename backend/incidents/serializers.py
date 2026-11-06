from rest_framework import serializers

from .models import Incident


class IncidentListFilters(serializers.Serializer):
    ordering = serializers.ChoiceField(choices=["-timestamp", "timestamp"], default="-timestamp")


class IncidentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    description = serializers.CharField(
        min_length=10,
        error_messages={
            key: "La descripción debe tener al menos 10 caracteres."
            for key in ("required", "blank", "null", "min_length")
        },
    )

    class Meta:
        model = Incident
        fields = ["id", "description", "category", "timestamp", "user", "user_name"]
        read_only_fields = ["id", "timestamp", "user"]

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - {"description", "category"}
            if unknown:
                raise serializers.ValidationError(
                    {key: "Campo no permitido." for key in unknown}
                )
        return super().to_internal_value(data)
