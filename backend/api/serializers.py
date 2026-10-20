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
        accounts = User.objects.filter(email__iexact=email)
        if self.instance:
            accounts = accounts.exclude(pk=self.instance.pk)
        if accounts.exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return email

    # Toda contraseña nueva debe contener letras y números, además de la longitud mínima.
    def validate_password(self, value):
        if not any(character.isalpha() for character in value) or not any(character.isdigit() for character in value):
            raise serializers.ValidationError("La contraseña debe contener letras y números.")
        return value

    # Reutiliza el gestor para guardar el hash de Django, nunca la contraseña recibida.
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# Reutiliza las validaciones y permite restablecer la contraseña sin incluirla en respuestas.
class UserUpdateSerializer(UserSerializer):
    # Permite editar el estado; la contraseña es opcional y el identificador no se modifica.
    class Meta(UserSerializer.Meta):
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {**UserSerializer.Meta.extra_kwargs["password"], "required": False},
        }

    # Estas comprobaciones se ejecutan dentro de la misma transacción que guarda el cambio.
    def validate(self, attrs):
        account = self.instance
        active = attrs.get("is_active", account.is_active)
        role = attrs.get("role", account.role)
        if account.pk == self.context["request"].user.pk and not active:
            raise serializers.ValidationError({"is_active": "No puede desactivar su propia cuenta."})

        was_admin = account.is_active and account.role == User.Role.ADMINISTRADOR_SISTEMA
        remains_admin = active and role == User.Role.ADMINISTRADOR_SISTEMA
        if was_admin and not remains_admin:
            other_admins = User.objects.filter(
                is_active=True, role=User.Role.ADMINISTRADOR_SISTEMA,
            ).exclude(pk=account.pk)
            if not other_admins.exists():
                raise serializers.ValidationError(
                    "Debe conservar al menos un Administrador de sistema activo."
                )
        return attrs

    # Genera el hash antes de guardar; si no se envía contraseña, conserva la actual.
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            instance.set_password(password)
        return super().update(instance, validated_data)
