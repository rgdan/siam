# Frontend de SIAM

Interfaz en Vue y Vite.

## Docker

La [guía de Docker](../README.md#docker) inicia el frontend y el backend juntos, sin instalar Node.js ni Python en el equipo. Abra **http://127.0.0.1:5173/**. La conexión con la API ya está configurada; no necesita crear `frontend/.env`.

Para trabajar sin contenedores, consulte la [guía de desarrollo local](../docs/development.md).

## Acceso

| Ruta | Uso |
| :--- | :--- |
| `/` | Información pública del museo |
| `/login` | Inicio de sesión del personal; abre el calendario |
| `/interno/usuarios` | Administración de cuentas, para el administrador de sistema |

Para probar los roles y el escenario del **23–29 de noviembre de 2026**, consulte la [carga de datos y cuentas de demostración](../backend/README.md#datos-de-demostración). Son solo para desarrollo local.
