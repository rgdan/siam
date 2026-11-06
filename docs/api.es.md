# API de SIAM

[Proyecto](../README.md)

La API recibe solicitudes HTTP y devuelve respuestas JSON. Puede consumirla desde el frontend, curl, Postman o cualquier cliente HTTP. Swagger UI es una herramienta opcional para consultar la documentación y probar solicitudes.

El esquema OpenAPI describe los endpoints, sus campos, filtros y respuestas en un formato que otras herramientas pueden leer. drf-spectacular lo genera desde las vistas y serializadores de Django. Swagger usa ese archivo para mostrar la referencia; el esquema no modifica la base de datos ni sustituye la API.

| Referencia | Dirección |
| :--- | :--- |
| Swagger UI local | [127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) |
| Esquema OpenAPI local | [127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/) |
| Referencia publicada | [rgdan.github.io/siam](https://rgdan.github.io/siam/) |

Inicie el sistema con la [guía de Docker](../README.md#docker). Para aplicar las nuevas dependencias, ejecute `docker compose up --build -d`.

## Autenticación

SIAM usa cookies de sesión y protección CSRF. El flujo es el mismo para cualquier cliente HTTP:

1. Ejecute `GET /api/auth/csrf/` para obtener la cookie y el token CSRF.
2. Ejecute `POST /api/auth/login/` con `email` y `password`. Puede usar una [cuenta de prueba](../README.md#cuentas-de-prueba).
3. Ejecute `GET /api/auth/me/` para consultar la cuenta y sus permisos.
4. Pruebe un endpoint permitido por su rol y cierre la sesión con `POST /api/auth/logout/`.

El cliente debe conservar las cookies `sessionid` y `csrftoken`, y enviar el token CSRF actual en el encabezado `X-CSRFToken` de las escrituras, incluido el inicio de sesión. El token cambia al iniciar sesión, por lo que debe usar el nuevo valor para las solicitudes siguientes. El navegador administra las cookies automáticamente; curl y Postman deben configurarse para conservarlas.

Si usa Swagger UI local, su configuración lee la cookie CSRF y agrega el encabezado. El diálogo Authorize no establece cookies de sesión; autentíquese mediante `/api/auth/login/`.

La consulta de eventos públicos, configuración pública, salud del servicio y token CSRF no requiere sesión. Crear un evento en `/api/events/` sí requiere autenticación y permiso. La descripción de cada operación indica el permiso; `/api/auth/me/` devuelve los de la cuenta actual.

## Convenciones

- Las solicitudes y respuestas normales usan JSON. Las fotografías se envían como contenido base64 en JSON, no como archivos multipart.
- Las fechas y horas incluyen zona horaria. Los filtros de reportes usan `YYYY-MM-DD`, con límites inclusivos en `America/Costa_Rica`.
- El historial de incidencias muestra 20 registros por página y acepta `page` y `ordering` (`-timestamp` o `timestamp`). La bitácora muestra 50. Las demás listas no tienen paginación.
- Sin fechas, los reportes consolidados usan el mes actual. Las colecciones reflejan el inventario actual. Las exportaciones PDF/Excel incluyen todos los registros correspondientes.
- Los errores contienen mensajes por campo o `detail`/`non_field_errors`: `400` para datos inválidos, `401` sin sesión o con credenciales incorrectas, `403` por permisos/CSRF y `404` si no existe el recurso o la página. El registro de visitantes e incidencias puede devolver `503` si falla el guardado.

## GitHub Pages

El [workflow de documentación](../.github/workflows/api-docs.yml) valida el esquema en los pull requests. Al actualizar `main`, genera y publica la referencia si cambió el backend, la página de documentación o el workflow. También permite ejecución manual desde Actions; solo `main` despliega.

En **Settings → Pages → Build and deployment**, seleccione **GitHub Actions** como fuente. Incorpore el workflow a `main` y consulte **Actions → API documentation** para obtener la dirección publicada. Usa `GITHUB_TOKEN`, sin tokens personales ni secretos de producción.

La página publicada es de consulta. GitHub Pages aloja el HTML y el esquema; los recursos de Swagger se cargan desde una versión fija de jsDelivr. El backend y la base de datos permanecen en su equipo. Para ejecutar solicitudes, use cualquier cliente HTTP contra su API en ejecución; Swagger UI local también permite hacerlo.

## Actualizar la referencia

Al cambiar un endpoint, actualice sus anotaciones `@extend_schema` y serializadores. `backend/api/schema.py` describe las respuestas que las vistas construyen directamente. No incluya datos reales de cuentas, cookies ni secretos en los ejemplos.

Desde la raíz del repositorio:

```bash
docker compose exec backend python manage.py spectacular --file /tmp/openapi.yaml --validate --fail-on-warn
docker compose cp backend:/tmp/openapi.yaml ./openapi.yaml
```

El archivo generado no necesita incluirse en Git. CI lo genera sin iniciar el backend ni acceder a una base de datos, y falla si encuentra advertencias en el esquema.

Referencias: [personalización de drf-spectacular](https://drf-spectacular.readthedocs.io/en/stable/customization.html), [workflows de GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
