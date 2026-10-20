# Frontend de SIAM

Vue + Vite. Requiere Node.js 22.18 o posterior.

Desde la raíz del repositorio:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abra http://127.0.0.1:5173/. La página consulta la API al cargar.
Con el backend activo muestra `Conectado`; sin él muestra un error.

La dirección de la API está en `.env`, en `VITE_API_BASE_URL`, y debe terminar
en `/`. Reinicie Vite si la cambia.

Para generar la versión de producción: `npm run build`.
