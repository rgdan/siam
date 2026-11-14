from datetime import date
import re
from rest_framework import serializers


# SIAM-17: valida las fechas opcionales del reporte.
def validar_fecha_reporte(valor, campo):
    if valor is None or valor == "":
        return None

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise serializers.ValidationError({
            campo: "La fecha debe tener el formato AAAA-MM-DD."
        })

    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise serializers.ValidationError({
            campo: "Ingrese una fecha válida."
        }) from None

