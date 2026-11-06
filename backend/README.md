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

## Reinicio del historial de migraciones

Cada aplicación tiene una única migración `0001_initial` con el esquema actual. Las bases de datos creadas con el historial anterior no son compatibles. Para reiniciar el entorno local, detenga el backend, elimine `backend/db.sqlite3` y sus archivos `-wal` y `-shm` si existen, y ejecute de nuevo `python manage.py migrate` y `python cargar_datos_demo.py` desde `backend/`. Este proceso elimina todos los datos locales.

## Datos de demostración

Después de aplicar las migraciones, desde `backend/`, con `.venv` activo y `DJANGO_SECRET_KEY` definido:

```bash
python cargar_datos_demo.py
```

El script carga cinco cuentas, nueve piezas de distintas colecciones con dos imágenes de ejemplo cada una, quince eventos públicos y privados (incluido uno cancelado), 134 ingresos, cinco incidencias, los parámetros de configuración y sus registros de auditoría. Las piezas cubren almacenamiento, exhibición, préstamo, baja, robo y extravío. Todos los datos son sintéticos; las imágenes son ilustraciones de muestra.

El escenario se concentra en la semana del **23 al 29 de noviembre de 2026**, en la zona horaria de Costa Rica. Incluye eventos el 20 y 30 de noviembre y cuatro eventos del 3–4 de noviembre para mostrar reportes de asistencia desde ahora. La asistencia solo se precarga en eventos cuya fecha ya pasó al ejecutar el script; los futuros quedan pendientes para registrarla desde la interfaz. Los registros de visitantes e incidencias representan el escenario de esa semana, aunque se carguen antes.

Todas las cuentas usan la contraseña `Demo12345`. Ingrese por `/login` en el frontend.

| Rol | Correo |
|---|---|
| Guarda | `guarda@demo.siam.test` |
| Coordinador | `coordinador@demo.siam.test` |
| Museólogo | `museologo@demo.siam.test` |
| Administrador general | `administrador_general@demo.siam.test` |
| Administrador de sistema | `administrador_sistema@demo.siam.test` |

Puede repetir el script: conserva los registros existentes, sus cambios y contraseñas, sin duplicar los datos ya cargados. Tampoco reemplaza la configuración existente. La carga se ejecuta en una transacción: si falla, no deja datos parciales. Utilícelo solo en desarrollo local, nunca en producción.

## Endpoint

En Postman: `GET http://127.0.0.1:8000/api/health/`.

Respuesta: `200 OK` con `{"estado":"ok"}`. Solo comprueba que el servidor responde.


