from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio.")
        user = self.model(email=self.normalize_email(email.strip()), **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
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
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

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

    def __str__(self):
        return self.email
