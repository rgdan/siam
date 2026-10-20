from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


# Centraliza la creación de cuentas para validar sus datos y guardar contraseñas como hashes.
class UserManager(BaseUserManager):
    # Normaliza el correo, genera el hash de la contraseña y valida antes de guardar.
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio.")
        user = self.model(email=self.normalize_email(email.strip()), **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user


# Representa una cuenta interna y reutiliza la gestión de contraseñas de Django.
class User(AbstractBaseUser):
    # Define los cinco roles posibles; cada cuenta almacena solo uno.
    class Role(models.TextChoices):
        GUARDA = "guarda", "Guarda"
        COORDINADOR = "coordinador", "Coordinador"
        MUSEOLOGO = "museologo", "Museólogo"
        ADMINISTRADOR_GENERAL = "administrador_general", "Administrador general"
        ADMINISTRADOR_SISTEMA = "administrador_sistema", "Administrador de sistema"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=25, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    # Configura restricciones de la tabla, no campos adicionales de la cuenta.
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=[
                    "guarda", "coordinador", "museologo",
                    "administrador_general", "administrador_sistema",
                ]),
                name="user_valid_role",
            ),
        ]

    # Incluye relaciones ocultas y gestores sin filtros para no borrar registros asociados.
    def has_related_records(self):
        return any(
            relation.related_model._base_manager.filter(**{relation.field.name: self}).exists()
            for relation in self._meta.get_fields(include_hidden=True)
            if relation.auto_created and not relation.concrete
            and (relation.one_to_many or relation.one_to_one)
        )

    # Identifica la cuenta por su correo cuando Django muestra el objeto como texto.
    def __str__(self):
        return self.email
