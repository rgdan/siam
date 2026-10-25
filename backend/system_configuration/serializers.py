import re

from rest_framework import serializers


class Hours(serializers.Serializer):
    opens = serializers.CharField(allow_null=True)
    closes = serializers.CharField(allow_null=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {k: "Campo desconocido." for k in unknown}
                )
        return super().to_internal_value(data)

    def validate(self, attrs):


        missing = set(self.fields) - attrs.keys()
        if missing:
            raise serializers.ValidationError(
                {key: "Este campo es obligatorio." for key in missing}
            )
        errors = {}
        for key, value in attrs.items():
            if value is not None and not re.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d", value
            ):
                errors[key] = "Use HH:MM (00:00 a 23:59)."
        if errors:
            raise serializers.ValidationError(errors)
        start, end = attrs["opens"], attrs["closes"]
        if (start is None) != (end is None):
            raise serializers.ValidationError(
                {"closes": "Indique ambas horas o null para día cerrado."}
            )
        if start is not None and end <= start:
            raise serializers.ValidationError(
                {"closes": "El cierre debe ser posterior a la apertura."}
            )
        return attrs


class ConfigurationSerializer(serializers.Serializer):
    museum_name = serializers.CharField(max_length=200)
    address = serializers.CharField(max_length=500)
    location = serializers.CharField(max_length=500)
    opening_hours = serializers.DictField(child=Hours())
    default_language = serializers.ChoiceField(choices=["es", "en"])

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {k: "Parámetro desconocido." for k in unknown}
                )
        return super().to_internal_value(data)

    def validate_opening_hours(self, value):
        if set(value) != set(map(str, range(7))):
            raise serializers.ValidationError(
                "Incluya los siete días: 0=domingo, 1=lunes, …, 6=sábado."
            )
        return value
