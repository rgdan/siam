# Backend de SIAM

API REST en Django. Responde JSON y funciona sin el frontend.

## Instalar y ejecutar

Requiere Python 3.10 o posterior. Desde la raíz del repositorio, en Bash:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex())')"
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

En una terminal nueva, active `.venv` y vuelva a definir `DJANGO_SECRET_KEY`.
Use una clave estable para conservar las sesiones entre reinicios; no la suba al repositorio.

Para salir del entorno virtual, detenga el servidor con `Ctrl+C` y ejecute `deactivate`.

## Cuentas de prueba

Después de aplicar las migraciones, desde `backend/`, con `.venv` activo y `DJANGO_SECRET_KEY` definido:

```bash
python crear_usuarios_demo.py
```

Todas usan la contraseña `Demo12345`. Ingrese por `/login` en el frontend.

| Rol | Correo |
|---|---|
| Guarda | `guarda@demo.siam.test` |
| Coordinador | `coordinador@demo.siam.test` |
| Museólogo | `museologo@demo.siam.test` |
| Administrador general | `administrador_general@demo.siam.test` |
| Administrador de sistema | `administrador_sistema@demo.siam.test` |

Puede repetir el script: conserva las cuentas existentes sin cambiar sus datos ni contraseñas.
Utilícelas solo en desarrollo local, nunca en producción.

## Endpoint

En Postman: `GET http://127.0.0.1:8000/api/health/`.

Respuesta: `200 OK` con `{"estado":"ok"}`. Solo comprueba que el servidor responde.


