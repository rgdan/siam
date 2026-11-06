# Backend de SIAM

API REST en Django y SQLite.

## Docker

Para iniciar todo el sistema, siga la [guía de Docker](../README.md#docker).

El volumen de Docker usa una base independiente de `backend/db.sqlite3`.

Para trabajar sin contenedores, consulte la [guía de desarrollo local](../docs/development.md).

## Datos de demostración

Desde la raíz del repositorio:

```bash
docker compose exec backend python cargar_datos_demo.py
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

## Endpoint

`GET http://127.0.0.1:8000/api/health/` devuelve `200 OK` con `{"estado":"ok"}` si el servidor responde.

La [referencia de la API](../docs/api.es.md) incluye [Swagger UI local](http://127.0.0.1:8000/api/docs/), el esquema OpenAPI y el flujo de autenticación. Las anotaciones de las vistas y los serializadores generan la documentación; GitHub Actions la valida y publica en Pages desde `main`.
