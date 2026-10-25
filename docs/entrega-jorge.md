


## SIAM-33 · RF-ADS-04

`audit.services.record` es el único escritor recomendado. Guarda usuario, rol en el momento de la acción, fecha con zona horaria, acción, entidad e identificador textual (admite UUID), y diferencias `{campo: {old, new}}`.
Acciones: `create`, `modify`, `decommission`, `sensitive_read`, `login`, `failed_login`.
Los intentos fallidos conocidos guardan la cuenta y su rol; los desconocidos tienen usuario nulo, rol e id vacíos. Nunca se guarda la contraseña ni el correo arbitrario enviado por un desconocido.
Los nombres de campos con password/passwd/contraseña/token/secret se excluyen recursivamente; `snapshot` tampoco incluye binarios. Entregar campos de dominio explícitos: no poner contraseñas bajo claves genéricas ni enviar cuerpos de solicitud completos al helper.

### Integración con visitantes y eventos de Sprint 2

```python
from audit.services import audited_create

# Dentro de la vista, después de validar datos y permisos:
visitor = audited_create(user=request.user, entity="visitor_entry", create=serializer.save)
event = audited_create(user=request.user, entity="event", create=event_serializer.save)
```

Cada llamada ejecuta el callback y crea exactamente una entrada en la misma transacción. Los callbacks guardan sus relaciones, pero no escriben otra entrada en la bitácora. No hay señales ni middleware que dupliquen registros.
Las tablas de visitantes y eventos todavía no existen: las pruebas verifican este contrato con un modelo sustituto; las vistas de esas historias deben llamar al helper cuando se implementen.
La creación de cuentas ya usa ese helper. Login, login fallido y edición de cuentas ya llaman a la bitácora.

Para otras modificaciones o lecturas sensibles:

```python
from django.db import transaction
from audit.services import record, snapshot

with transaction.atomic():
    piece = Piece.objects.select_for_update().get(pk=piece_id)
    before = snapshot(piece)
    piece.title = "Título corregido"
    piece.save()
    record(user=request.user, action_type="modify", entity="piece",
           entity_id=piece.pk, old=before, new=snapshot(piece))

record(user=request.user, action_type="sensitive_read", entity="piece", entity_id=piece.pk)
```

`GET /api/audit/?user=1&action_type=modify&entity=piece&date_from=2026-10-01&date_to=2026-10-31&page=1`

Devuelve `{count, next, previous, results}`, 50 registros por página, del más reciente al más antiguo, con desempate por id. Las fechas son inclusivas, formato `YYYY-MM-DD`, zona `America/Costa_Rica`. Filtros inválidos: 400.
Solo `administrador_sistema` activo: los otros cuatro roles y el público reciben 403. No hay rutas para editar ni eliminar entradas; los métodos de escritura en la lista devuelven 405 para el administrador. El modelo y su queryset rechazan ediciones y borrados. Esto no pretende impedir que un operador con acceso SQL directo cambie la base.

## SIAM-36 · RNF-03

`collection_integrity.services.collection_transaction()` envuelve `transaction.atomic()`. Los servicios `register_piece`, `edit_piece`, `decommission_piece`, `loan_piece` y `change_piece_state` incluyen pieza, fotos, historial y auditoría en la misma transacción. Para actualizar se bloquea la pieza con `select_for_update`; SQLite usa el modo `IMMEDIATE` ya configurado en el esqueleto.

`Piece`, `Photo` y `PieceHistory` son un agregado mínimo de integración: Sprint 2 debe ampliar o integrar estos modelos con su esquema definitivo, sin duplicar tablas. No se añadieron endpoints de colección ni reglas de préstamo ajenas a estas historias. Las vistas futuras deben validar datos y permisos antes de invocar los servicios. Los servicios internos no sustituyen el RBAC de la vista.

```python
from collection_integrity.services import register_piece, edit_piece
piece = register_piece(user=request.user, title="Vasija",
                       photos=[{"name": "frente.jpg", "content": uploaded.read()}])
edit_piece(user=request.user, piece_id=piece.pk, title="Vasija restaurada")
```

Para operaciones nuevas: abrir `collection_transaction`, guardar todos los pasos y registrar una sola entrada al final. Capturar excepciones fuera del bloque; no ocultarlas dentro de él. Usar una sola conexión/base de datos.
Las fotos del módulo se guardan como binarios en la base para incluirlas realmente en el rollback. Si Sprint 2 usa disco/S3, una transacción de Django no revierte esos archivos: necesitará staging y compensación o publicación tras `transaction.on_commit`, manteniendo las filas dentro de la transacción. Notificaciones y otros efectos externos también deben publicarse después del commit.

### Prueba 1: excepción a mitad de registro

Automatizada en `tests.test_collection_integrity.CollectionIntegrityTests.test_exception_halfway_registration_leaves_no_rows`.
Se crea la pieza, se escribe la primera foto y se fuerza una excepción al intentar escribir la segunda. Resultado esperado y verificado: **0 piezas, 0 fotos, 0 historiales y 0 auditorías**.
Además se comprueba rollback en edición, baja, préstamo y cambio de estado cuando falla el historial, y en registro cuando falla después de crear la auditoría.

### Prueba 2: terminar el servidor durante una escritura

Ejecutar `python backend/tests/crash_probe.py`. El script crea una base SQLite temporal, aplica migraciones y confirma una pieza con su foto, historial y auditoría. Inicia un servidor WSGI de Django local en un puerto libre y hace una escritura HTTP.
La solicitud escribe las cuatro tablas dentro de una transacción externa y marca un checkpoint antes del commit. El proceso padre espera ese checkpoint, termina **solo el proceso hijo que creó**, lo reinicia sobre la misma base y consulta los datos por HTTP.
Las rutas de prueba viven exclusivamente en `tests.crash_urls`; nunca se incluyen en las URLs de producción. La base real no se modifica.
Resultado esperado y verificado: la pieza `committed` y el contenido `intact` de su foto siguen intactos; conteos antes/después `[1, 1, 1, 1]`; ningún registro de `interrupted`. El script falla con código no cero ante diferencias, no depende de adivinar cuánto tarda la escritura y limpia sus recursos.
La prueba valida SQLite, que es el motor actual. Repetir sobre el motor final si el equipo migra a PostgreSQL; no equivale a una prueba de corte eléctrico del equipo.

## SIAM-32 · RF-ADS-03

- `GET /api/configuration/`: `{values, defaults}` para el administrador de sistema.
- `PATCH /api/configuration/`: uno o más parámetros, mismo formato de respuesta.
- `POST /api/configuration/<key>/reset/`: acción **Restaurar valor por defecto**, devuelve valores vigentes.
- `GET /api/public/configuration/`: solo valores públicos, sin sesión y sin caché.

Los endpoints administrativos devuelven 403 para los demás roles y el público. Son contratos JSON para la futura pantalla administrativa de Vue; esta entrega no añade una pantalla administrativa.

Parámetros: `museum_name`, `address`, `location`, `opening_hours`, `default_language` (`es` o `en`). Todos tienen valores por defecto definidos en `system_configuration/defaults.py`, coherentes con la página pública existente. No se depende de reinicios ni de caché de proceso: cada consulta lee la base.

Ejemplo de PATCH:

```json
{"museum_name": "Museo SIAM", "default_language": "en"}
```

`opening_hours` es un objeto completo de siete días (`0` domingo a `6` sábado); cada día tiene `opens` y `closes` en `HH:MM`, o ambos `null` si cierra. No se aceptan horas inválidas, cierre anterior/igual a apertura, días incompletos, idioma desconocido, campos desconocidos ni textos vacíos.
Los errores 400 están asociados al campo. Por ejemplo, el frontend puede mostrar el mensaje de `opening_hours.2.closes` debajo del cierre del martes. La validación precede a cualquier escritura; no se guardan parcialmente los parámetros.
Cada parámetro que cambia genera una entrada `modify`, entidad `system_parameter`, id igual a su clave, con el valor anterior/nuevo, actor y fecha. Restaurar también audita si cambia el valor; reenviar el valor vigente no crea un cambio ficticio.

`MuseoPublico.vue` consulta el endpoint público en cada carga y aplica nombre, dirección/ubicación, horarios e idioma por defecto. Una preferencia de idioma explícita del visitante se respeta. Si falla la API se avisa y se muestran los datos de referencia existentes.

## Referencias técnicas

- [Django: transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)
- [DRF: permisos](https://www.django-rest-framework.org/api-guide/permissions/)
- [DRF: paginación](https://www.django-rest-framework.org/api-guide/pagination/)
