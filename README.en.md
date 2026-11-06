<div align="center">

![SIAM · Sistema de Información y Analítica Museal · Museum Information and Analytics System](docs/assets/siam-banner.svg)

**Museo Histórico Cultural Juan Santamaría · Alajuela, Costa Rica**

[Español](README.md) · [English](README.en.md) · [Frontend](frontend/README.md) · [Backend](backend/README.md)

**Vue 3** &nbsp; / &nbsp; **Vite** &nbsp; / &nbsp; **Django REST Framework** &nbsp; / &nbsp; **SQLite**

Academic project in development<br>
Software Requirements · Tecnológico de Costa Rica

</div>

---

**SIAM** manages visitors, events, and collections for the Museo Histórico Cultural Juan Santamaría, with public information and role-based administrative access.

| Module | Functionality |
| :--- | :--- |
| **Public information** | Find museum information, opening hours, events, and the privacy policy. |
| **Visitors** | Record entries by age group, nationality category, and sex, without requesting visitors' names or identity numbers. |
| **Events** | Browse the calendar, manage activities, and record actual attendance. |
| **Incidents** | Browse paginated history, sort by date, and report new incidents. |
| **Collections** | Manage pieces, photos, locations, loans, decommissions, and theft or loss records. |
| **Reports** | View attendance and consolidated reports with incidents by category; export PDF and Excel files according to permissions. |
| **Administration** | Manage accounts, roles, museum configuration, and the activity audit log. |

The interface supports **Spanish and English**, **light and dark themes**, and layouts that adapt to mobile devices. Internal access uses sessions and role permissions: guard, coordinator, museologist, general administrator, and system administrator.

## Gallery

Screenshots with demo data. Select an image to view it at full size.

| Museum information | Event calendar |
| :---: | :---: |
| [![Museum information](docs/assets/screenshots/museum.png)](docs/assets/screenshots/museum.png) | [![Event calendar](docs/assets/screenshots/calendar.png)](docs/assets/screenshots/calendar.png) |
| **Collection** | **Incidents** |
| [![Collection](docs/assets/screenshots/collection.png)](docs/assets/screenshots/collection.png) | [![Incidents](docs/assets/screenshots/incidents.png)](docs/assets/screenshots/incidents.png) |
| **Visitor registration** | **Consolidated reports** |
| [![Visitor registration](docs/assets/screenshots/visitors.png)](docs/assets/screenshots/visitors.png) | [![Consolidated reports](docs/assets/screenshots/reports.png)](docs/assets/screenshots/reports.png) |

## Docker

Requires Docker with Compose. Python and Node.js do not need to be installed on the host.

**First run:** copy `.env.example` to `.env` and set `DJANGO_SECRET_KEY` to a random key of at least 32 characters. You can generate one with `openssl rand -hex 32`. This file is separate from `frontend/.env` and is excluded from Git.

From the repository root:

```bash
docker compose up --build -d
docker compose exec backend python cargar_datos_demo.py
```

Open **http://127.0.0.1:5173/**. Migrations run when the backend starts; the second command loads demo data.

| Action | Command |
| :--- | :--- |
| View logs | `docker compose logs -f` |
| Stop | `docker compose down` |
| Start again | `docker compose up -d` |
| Apply code or dependency changes | `docker compose up --build -d` |

SQLite uses its own volume, separate from `backend/db.sqlite3`. Stopping or recreating containers preserves the data. `docker compose down -v` deletes the volume and its data.

This setup is for local development and demonstrations; it uses Django's and Vite's development servers.

For development without containers, see the [local development guide](docs/development.en.md).

## Test accounts

The script loads role accounts, pieces with sample images, events, visitor entries, incidents, and configuration for **November 23–29, 2026**. Earlier events support attendance report demonstrations. Rerunning it preserves existing records without duplicates or overwrites; see the [scenario details (Spanish)](backend/README.md#datos-de-demostración).

All accounts use the password **`Demo12345`** and are **for local development only**.

| Role | Email |
| :--- | :--- |
| Guard | `guarda@demo.siam.test` |
| Coordinator | `coordinador@demo.siam.test` |
| Museologist | `museologo@demo.siam.test` |
| General administrator | `administrador_general@demo.siam.test` |
| System administrator | `administrador_sistema@demo.siam.test` |

## Repository structure

```text
siam/
├── frontend/                  Vue interface
│   └── src/
│       ├── components/        Screens and forms
│       ├── i18n/              Spanish and English
│       └── theme/             Light and dark themes
├── backend/                   Django REST API
│   ├── api/                   Authentication, events, reports
│   ├── visitors/              Visitor records
│   ├── incidents/             Incident records
│   ├── collection_integrity/  Museum collection
│   ├── audit/                 Activity log
│   └── system_configuration/  Museum settings
└── docs/assets/               README artwork
```
