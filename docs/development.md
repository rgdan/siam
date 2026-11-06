# Desarrollo sin Docker

[Español](development.md) · [English](development.en.md) · [README](../README.md)

Requisitos: **Python 3.10 o posterior**, **Node.js 22.18 o posterior** y **npm**. Ejecute los comandos en Bash desde la raíz del repositorio, en dos terminales separadas.

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex())')"
python manage.py migrate
python cargar_datos_demo.py
python manage.py runserver 127.0.0.1:8000
```

Reutilice `DJANGO_SECRET_KEY` para conservar las sesiones entre reinicios. No incluya la clave en el repositorio.

**Frontend**

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Abra **[127.0.0.1:5173](http://127.0.0.1:5173/)**. El personal ingresa por **[/login](http://127.0.0.1:5173/login)** y accede directamente al calendario de eventos.

Use `127.0.0.1` en ambos servidores. `VITE_API_BASE_URL` debe apuntar a `http://127.0.0.1:8000/api/`, incluida la barra final. Reinicie Vite si cambia esta variable.

## Conexión con la API

El archivo `frontend/.env` contiene:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/
```

Conserve la barra final y reinicie Vite si cambia el valor. Use el mismo host en ambos servidores: `127.0.0.1` o `localhost`.

## Compilación

Desde la raíz del repositorio:

```bash
cd frontend
npm run build
```

Genera los archivos de producción en `dist/`.
