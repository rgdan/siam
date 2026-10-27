from rest_framework import serializers

from .models import VisitorEntry


class VisitorEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorEntry
        fields = ["id", "age_group", "nationality", "sex", "timestamp", "user"]
        read_only_fields = ["id", "timestamp", "user"]

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - {"age_group", "nationality", "sex"}
            if unknown:
                raise serializers.ValidationError(
                    {key: "Campo no permitido." for key in unknown}
                )
        return super().to_internal_value(data)
