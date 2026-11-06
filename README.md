<div align="center">

![SIAM · Sistema de Información y Analítica Museal · Museum Information and Analytics System](docs/assets/siam-banner.svg)

**Museo Histórico Cultural Juan Santamaría · Alajuela, Costa Rica**

[Español](README.md) · [English](README.en.md) · [Frontend](frontend/README.md) · [Backend](backend/README.md)

**Vue 3** &nbsp; / &nbsp; **Vite** &nbsp; / &nbsp; **Django REST Framework** &nbsp; / &nbsp; **SQLite**

Proyecto académico en desarrollo<br>
Requerimientos del Software · Tecnológico de Costa Rica

</div>

---

**SIAM** es un sistema de gestión de visitantes, eventos y colecciones del Museo Histórico Cultural Juan Santamaría, con información pública y acceso administrativo por roles.

| Módulo | Funcionalidad |
| :--- | :--- |
| **Información pública** | Consultar la información del museo, horarios, eventos y política de privacidad. |
| **Visitantes** | Registrar ingresos por grupo de edad, nacionalidad y sexo, sin solicitar nombres ni cédulas de visitantes. |
| **Eventos** | Consultar el calendario, gestionar actividades y registrar la asistencia real. |
| **Incidencias** | Consultar el historial paginado, ordenar por fecha y registrar nuevas incidencias. |
| **Colecciones** | Gestionar piezas, fotografías, ubicaciones, préstamos, bajas y registros de robo o extravío. |
| **Reportes** | Consultar asistencia y reportes consolidados con incidencias por categoría; exportar en PDF y Excel según los permisos. |
| **Administración** | Gestionar cuentas, roles, configuración del museo y bitácora de actividad. |

La interfaz incluye **español e inglés**, **tema claro y oscuro** y navegación adaptable a dispositivos móviles. El acceso interno se controla mediante sesiones y permisos por rol: guarda, coordinador, museólogo, administrador general y administrador de sistema.

## Docker

Requiere Docker con Compose. No necesita instalar Python ni Node.js en el equipo.

**Primera vez:** copie `.env.example` como `.env` y defina `DJANGO_SECRET_KEY` con una clave aleatoria de al menos 32 caracteres. Puede generarla con `openssl rand -hex 32`. Este archivo es independiente de `frontend/.env` y no se sube al repositorio.

Desde la raíz del repositorio:

```bash
docker compose up --build -d
docker compose exec backend python cargar_datos_demo.py
```

Abra **http://127.0.0.1:5173/**. Las migraciones se aplican al iniciar el backend; los datos de demostración se cargan con el segundo comando.

| Acción | Comando |
| :--- | :--- |
| Ver registros | `docker compose logs -f` |
| Detener | `docker compose down` |
| Volver a iniciar | `docker compose up -d` |
| Aplicar cambios de código o dependencias | `docker compose up --build -d` |

SQLite se guarda en un volumen propio, separado de `backend/db.sqlite3`. Detener o recrear los contenedores conserva los datos. `docker compose down -v` elimina el volumen y sus datos.

Esta configuración es para desarrollo y demostraciones locales; usa los servidores de desarrollo de Django y Vite.

## Instalación sin Docker

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

El historial de migraciones se reinició. Si tiene una base de datos de una versión anterior, debe recrearla; consulte el [procedimiento de reinicio](backend/README.md#reinicio-del-historial-de-migraciones). Se perderán los datos locales.

**Frontend**

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Abra **[127.0.0.1:5173](http://127.0.0.1:5173/)**. El personal ingresa por **[/login](http://127.0.0.1:5173/login)** y accede directamente al calendario de eventos.

Use `127.0.0.1` en ambos servidores. `VITE_API_BASE_URL` debe apuntar a `http://127.0.0.1:8000/api/`, incluida la barra final. Reinicie Vite si cambia esta variable.

## Cuentas de prueba

El script carga cuentas por rol, piezas con imágenes de muestra, eventos, ingresos, incidencias y configuración para la semana del **23–29 de noviembre de 2026**. Incluye eventos anteriores para demostrar reportes de asistencia. Puede repetirse sin duplicar ni sobrescribir los registros existentes; consulte los [detalles del escenario](backend/README.md#datos-de-demostración).

Todas las cuentas usan la contraseña **`Demo12345`** y son **solo para desarrollo local**.

| Rol | Correo |
| :--- | :--- |
| Guarda | `guarda@demo.siam.test` |
| Coordinador | `coordinador@demo.siam.test` |
| Museólogo | `museologo@demo.siam.test` |
| Administrador general | `administrador_general@demo.siam.test` |
| Administrador de sistema | `administrador_sistema@demo.siam.test` |

## Estructura del repositorio

```text
siam/
├── frontend/                  Interfaz Vue
│   └── src/
│       Pantallas y formularios
│       Español e inglés
│       Temas claro y oscuro
├── backend/                   Django REST API
│   Acceso, eventos, reportes
│   Registro de visitantes
│   Registro de incidencias
│   Colección del museo
│   Bitácora
│   Configuración del museo
└── docs/assets/               Recursos del README
```
