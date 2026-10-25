import os

import django


# Crea cuentas de desarrollo sin modificar las que ya existen.
def crear_usuarios_demo():
    from api.models import User
    from audit.services import audited_create
    from django.db import transaction

    print("Solo para desarrollo local: estas cuentas usan una contraseña pública.")
    with transaction.atomic():
        for role, nombre in User.Role.choices:
            email = f"{role}@demo.siam.test"
            if User.objects.filter(email__iexact=email).exists():
                print(f"Ya existe, sin cambios: {email}")
                continue
            audited_create(
                user=None, entity="user",
                create=lambda: User.objects.create_user(
                    email=email, password="Demo12345",
                    full_name=f"Demo {nombre}", role=role,
                ),
            )
            print(f"Creada: {email} ({nombre})")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    crear_usuarios_demo()
