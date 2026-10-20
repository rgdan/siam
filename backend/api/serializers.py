from rest_framework import serializers

from .models import User


# Valida la creación de cuentas y excluye la contraseña de todas las respuestas.
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)

    # Expone solo estos campos; el identificador y el estado no se aceptan al crear.
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "role", "is_active", "password"]
        read_only_fields = ["id", "is_active"]
        extra_kwargs = {
            "password": {"write_only": True, "required": True, "min_length": 8, "trim_whitespace": False},
        }

    # Compara sin distinguir mayúsculas para evitar cuentas duplicadas por la escritura del correo.
    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return email

    # La contraseña inicial debe contener letras y números, además de la longitud mínima.
    def validate_password(self, value):
        if not any(character.isalpha() for character in value) or not any(character.isdigit() for character in value):
            raise serializers.ValidationError("La contraseña debe contener letras y números.")
        return value

    # Reutiliza el gestor para guardar el hash de Django, nunca la contraseña recibida.
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
