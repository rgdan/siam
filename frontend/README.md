# Frontend de SIAM

Interfaz en Vue y Vite. Requiere **Node.js 22.18 o posterior**.

## Docker

La [guía de Docker](../README.md#docker) inicia el frontend y el backend juntos, sin instalar Node.js ni Python en el equipo. Abra **http://127.0.0.1:5173/**. La conexión con la API ya está configurada; no necesita crear `frontend/.env`.

## Inicio local

Desde la raíz del repositorio:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abra **http://127.0.0.1:5173/**. Para usar las funciones del personal, inicie también el [backend](../backend/README.md#inicio-local).

## Acceso

| Ruta | Uso |
| :--- | :--- |
| `/` | Información pública del museo |
| `/login` | Inicio de sesión del personal; abre el calendario |
| `/interno/usuarios` | Administración de cuentas, para el administrador de sistema |

Para probar los roles y el escenario del **23–29 de noviembre de 2026**, consulte la [carga de datos y cuentas de demostración](../backend/README.md#datos-de-demostración). Son solo para desarrollo local.

## Conexión con la API

El archivo `.env` contiene:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/
```

Conserve la barra final y reinicie Vite si cambia el valor. Use el mismo host en ambos servidores: `127.0.0.1` o `localhost`.

## Compilación

```bash
npm run build
```

Genera los archivos de producción en `dist/`.
