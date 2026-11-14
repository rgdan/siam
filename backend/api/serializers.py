from django.utils import timezone
from rest_framework import serializers

from .models import Evento


# Valida los datos necesarios para registrar eventos.
class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = [
            "id",
            "fecha",
            "descripcion",
            "ubicacion",
            "tipo",
            "asistentes_esperados",
            "asistentes_reales",
            "estado",
            "creado_por",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "asistentes_reales",
            "estado",
            "creado_por",
            "creado_en",
            "actualizado_en",
        ]

    # Los eventos nuevos deben programarse para una fecha futura.
    def validate_fecha(self, value):
        if self.instance is None and value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha y hora del evento deben ser futuras."
            )

        return value

    # La descripción es obligatoria y no puede superar 500 caracteres.
    def validate_descripcion(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "La descripción del evento es obligatoria."
            )

        if len(value) > 500:
            raise serializers.ValidationError(
                "La descripción no puede superar los 500 caracteres."
            )

        return value

    # La ubicación no puede estar vacía.
    def validate_ubicacion(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "La ubicación del evento es obligatoria."
            )

        return value

    # Solo se aceptan cantidades enteras mayores o iguales a uno.
    def validate_asistentes_esperados(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Los asistentes esperados deben ser un entero mayor o igual a 1."
            )

        return value


# SIAM-15: valida los campos permitidos para modificar eventos.
class EventoUpdateSerializer(EventoSerializer):
    class Meta(EventoSerializer.Meta):
        pass

    def validate_fecha(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La nueva fecha y hora del evento deben ser futuras."
            )

        return value

    def validate(self, attrs):
        campos_permitidos = {
            "fecha",
            "descripcion",
            "ubicacion",
            "tipo",
            "asistentes_esperados",
        }

        datos = self.initial_data

        if not isinstance(datos, dict):
            raise serializers.ValidationError(
                "Debe enviar los datos del evento en un objeto."
            )

        campos_enviados = set(datos.keys())
        campos_no_permitidos = campos_enviados - campos_permitidos

        if campos_no_permitidos:
            raise serializers.ValidationError({
                "detail": (
                    "No se pueden modificar estos campos: "
                    + ", ".join(sorted(campos_no_permitidos))
                )
            })

        if not campos_enviados:
            raise serializers.ValidationError(
                "Debe indicar al menos un campo para modificar."
            )

        return attrs


# SIAM-16: registra o corrige la asistencia real de un evento.
class EventoAsistenciaSerializer(serializers.Serializer):
    asistentes_reales = serializers.IntegerField(
        min_value=0,
        max_value=2147483647,
    )

    def validate(self, attrs):
        datos = self.initial_data

        if (
            not isinstance(datos, dict)
            or set(datos.keys()) != {"asistentes_reales"}
        ):
            raise serializers.ValidationError(
                "Solo se permite enviar el campo asistentes_reales."
            )

        # Exigimos un número entero JSON, no texto, booleanos ni decimales.
        valor = datos["asistentes_reales"]

        if type(valor) is not int:
            raise serializers.ValidationError({
                "asistentes_reales": "Debe ser un número entero mayor o igual a 0."
            })

        return attrs
