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
python manage.py migrate --run-syncdb
python manage.py runserver 127.0.0.1:8000
```

En una terminal nueva, active `.venv` y vuelva a definir `DJANGO_SECRET_KEY`.
Use una clave estable para conservar las sesiones entre reinicios; no la suba al repositorio.

Para salir del entorno virtual, detenga el servidor con `Ctrl+C` y ejecute `deactivate`.

## Endpoint

En Postman: `GET http://127.0.0.1:8000/api/health/`.

Respuesta: `200 OK` con `{"estado":"ok"}`. Solo comprueba que el servidor responde.

## Login en Postman

Use `http://127.0.0.1:8000` y conserve las cookies de Postman.

1. Solicite `GET /api/auth/csrf/` y copie `csrfToken`.
2. Envíe `POST /api/auth/login/` con JSON `{"email":"su correo","password":"su contraseña"}`
   y el encabezado `X-CSRFToken` con ese token. Guarde el nuevo `csrfToken` de la respuesta.
3. Consulte `GET /api/auth/me/` para ver su cuenta. Sin sesión devuelve `401`.
4. Envíe `POST /api/auth/logout/` con el nuevo token en `X-CSRFToken` para cerrar sesión.

Necesita una cuenta creada con `User.objects.create_user(...)` desde `python manage.py shell`.
