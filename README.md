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
| **Colecciones** | Gestionar piezas, fotografías, ubicaciones, préstamos, bajas y registros de robo o extravío. |
| **Reportes** | Consultar reportes de asistencia y consolidados; exportar en PDF y Excel según los permisos. |
| **Administración** | Gestionar cuentas, roles, configuración del museo y bitácora de actividad. |

La interfaz incluye **español e inglés**, **tema claro y oscuro** y navegación adaptable a dispositivos móviles. El acceso interno se controla mediante sesiones y permisos por rol: guarda, coordinador, museólogo, administrador general y administrador de sistema.

## Instalación local

Requisitos: **Python 3.10 o posterior**, **Node.js 22.18 o posterior** y **npm**. Ejecute los comandos en Bash desde la raíz del repositorio, en dos terminales separadas.

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex())')"
python manage.py migrate
python crear_usuarios_demo.py
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

## Cuentas de prueba

El script de desarrollo crea una cuenta por rol y conserva las cuentas existentes. Todas usan la contraseña **`Demo12345`** y son **solo para desarrollo local**.

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
