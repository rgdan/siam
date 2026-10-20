# Frontend de SIAM

Vue + Vite. Requiere Node.js 22.18 o posterior.

Desde la raíz del repositorio:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abra http://127.0.0.1:5173/. La página comprueba la sesión al cargar.
Sin sesión, muestra `/login`; al ingresar, abre `/interno` con su nombre y la opción
de cerrar sesión. Necesita el backend activo y una cuenta creada.

La dirección de la API está en `.env`, en `VITE_API_BASE_URL`, y debe terminar
en `/`. Reinicie Vite si la cambia.

Para generar la versión de producción: `npm run build`.

Use el mismo host para ambos servidores: `127.0.0.1` o `localhost`, sin mezclarlos.
