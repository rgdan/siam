# Frontend de SIAM

Vue + Vite. Requiere Node.js 22.18 o posterior.

Desde la raíz del repositorio:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abra http://127.0.0.1:5173/ para consultar la información pública.
Ingrese por `/login` para abrir el calendario de eventos. Necesita el backend activo y una cuenta creada.
Como administrador de sistema, abra **Usuarios** para crear, editar, restablecer contraseñas o eliminar cuentas.

Para generar una cuenta de prueba por rol, ejecute `python crear_usuarios_demo.py` desde `backend/`,
con su entorno virtual activo y `DJANGO_SECRET_KEY` definido ([instrucciones y correos](../backend/README.md#cuentas-de-prueba)).
Ingrese con `administrador_sistema@demo.siam.test` y `Demo12345` para administrar usuarios.
Estas cuentas son solo para desarrollo local; el script no modifica cuentas existentes.

La dirección de la API está en `.env`, en `VITE_API_BASE_URL`, y debe terminar
en `/`. Reinicie Vite si la cambia.

Para generar la versión de producción: `npm run build`.

Use el mismo host para ambos servidores: `127.0.0.1` o `localhost`, sin mezclarlos.
