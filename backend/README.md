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

En una terminal nueva, activa `.venv` y vuelve a definir `DJANGO_SECRET_KEY`.

## Endpoint

En Postman: `GET http://127.0.0.1:8000/api/health/`.

Respuesta: `200 OK` con `{"estado":"ok"}`. Solo comprueba que el servidor responde.

