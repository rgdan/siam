# Backend de SIAM

API REST en Django y SQLite. Requiere **Python 3.10 o posterior**.

## Inicio local

**1. Instalar.** Desde la raíz del repositorio, en Bash:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**2. Preparar la base de datos.**

```bash
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex())')"
python manage.py migrate
```

**3. Iniciar la API.**

```bash
python manage.py runserver 127.0.0.1:8000
```

La API queda disponible en **http://127.0.0.1:8000/api/**.

En una terminal nueva, active `.venv` y defina `DJANGO_SECRET_KEY` de nuevo. Reutilice la misma clave para conservar las sesiones; no la suba al repositorio.

Para detenerlo: `Ctrl+C`. Para salir del entorno virtual: `deactivate`.

## Datos de demostración

Desde `backend/`, con el entorno virtual y la clave activos:

```bash
python cargar_datos_demo.py
```

Carga el escenario del **23–29 de noviembre de 2026** y las cuentas de prueba. Puede repetirse sin duplicar ni sobrescribir los registros existentes. Si falla, se revierte toda la carga.

**Solo para desarrollo local.** Todos los datos e imágenes son sintéticos.

<details>
<summary>Contenido del escenario</summary>

| Datos | Contenido |
| :--- | :--- |
| Cuentas | 5, una por rol |
| Colecciones | 9 piezas y 18 imágenes de muestra |
| Eventos | 15 públicos y privados, incluido uno cancelado |
| Visitantes | 134 ingresos |
| Incidencias | 5, una por categoría |
| Configuración | Parámetros del museo y registros de auditoría |

Las piezas cubren almacenamiento, exhibición, préstamo, baja, robo y extravío.

Las fechas usan la zona horaria de Costa Rica. Además de la semana principal, hay eventos el 20 y 30 de noviembre y cuatro del 3–4 de noviembre para los reportes de asistencia.

La asistencia se precarga solo en eventos pasados al ejecutar el script. Los futuros quedan pendientes para registrarla desde la interfaz. Los ingresos e incidencias representan la semana de demostración, aunque se carguen antes.

</details>

<details>
<summary>Cuentas y contraseña</summary>

Contraseña para todas las cuentas nuevas: **`Demo12345`**. Ingrese por `/login` en el frontend.

| Rol | Correo |
|---|---|
| Guarda | `guarda@demo.siam.test` |
| Coordinador | `coordinador@demo.siam.test` |
| Museólogo | `museologo@demo.siam.test` |
| Administrador general | `administrador_general@demo.siam.test` |
| Administrador de sistema | `administrador_sistema@demo.siam.test` |

Las cuentas existentes conservan sus datos y contraseñas.

</details>

## Reinicio del historial de migraciones

<details>
<summary>Recrear una base de datos de una versión anterior</summary>

Cada aplicación tiene una única migración `0001_initial`. Las bases creadas con el historial anterior deben recrearse.

**Este proceso elimina todos los datos locales.**

1. Detenga el backend.
2. Elimine `backend/db.sqlite3` y sus archivos `-wal` y `-shm`, si existen.
3. Desde `backend/`, con `.venv` y `DJANGO_SECRET_KEY` activos, ejecute:

```bash
python manage.py migrate
python cargar_datos_demo.py
```

</details>

## Endpoint

`GET http://127.0.0.1:8000/api/health/` devuelve `200 OK` con `{"estado":"ok"}` si el servidor responde.
