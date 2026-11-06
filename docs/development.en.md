# Development without Docker

[Español](development.md) · [English](development.en.md) · [README](../README.en.md)

Requirements: **Python 3.10 or later**, **Node.js 22.18 or later**, and **npm**. Run the commands in Bash from the repository root, in two separate terminals.

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

Reuse `DJANGO_SECRET_KEY` to preserve sessions across restarts. Keep the key out of the repository.

The migration history has been reset. Databases from earlier versions must be recreated; see the [reset procedure (Spanish)](development.md#reinicio-del-historial-de-migraciones). This deletes local data.

**Frontend**

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open **[127.0.0.1:5173](http://127.0.0.1:5173/)**. Staff sign in at **[/login](http://127.0.0.1:5173/login)** and go directly to the event calendar.

Use `127.0.0.1` for both servers. Set `VITE_API_BASE_URL` to `http://127.0.0.1:8000/api/`, including the trailing slash. Restart Vite after changing it.

## Frontend build

```bash
cd frontend
npm run build
```

Vite writes production files to `dist/`.
