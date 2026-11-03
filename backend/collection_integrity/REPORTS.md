# Reporte de colección (SIAM-24 / RF-MUS-07)

Santiago puede reutilizar la misma función en SIAM-27:

```python
from collection_integrity.reports import collection_report_data

data = collection_report_data()
filtered = collection_report_data(state="missing", collection="Arqueología")
```

Endpoint: `GET /api/collection/report/`. Requiere sesión activa con rol **Museólogo**; otros roles reciben 403. La función interna no comprueba roles: el endpoint del reporte consolidado debe aplicar sus propios permisos.

Filtros opcionales: `state`, `object_type` y `collection`, combinables por coincidencia exacta. Omitir un filtro selecciona todos sus valores. `object_type=` y `collection=` seleccionan valores sin asignar. Estados aceptados: `displayed`, `stored`, `loaned`, `stolen`, `lost`, `missing` y `decommissioned`; `missing` agrupa Robada/Extraviada.

La respuesta JSON contiene:

- `generated_at`: fecha/hora ISO 8601 con zona horaria.
- `filters`: filtros aplicados (`null` significa todos).
- `total`: total de piezas para los filtros seleccionados.
- `active`: exhibición + almacenamiento + préstamo, sin bajas ni robos/extravíos.
- `by_state`: cinco categorías excluyentes: `displayed`, `stored`, `loaned`, `missing` y `decommissioned`.
- `missing_breakdown`: detalle de `stolen` y `lost`, incluido ya en `by_state.missing`.
- `by_object_type` y `by_collection`: mapas de nombre a cantidad; la clave vacía significa sin asignar.
- `available_filters`: tipos y colecciones de toda la colección, para conservar las opciones aunque un filtro no encuentre piezas.

Todos los conteos y opciones salen de una sola consulta agrupada, sin caché ni escrituras. Una baja se reconoce tanto por la bandera histórica `decommissioned=True` como por el estado `decommissioned`; tiene prioridad sobre el estado anterior para evitar contar la pieza como activa.

Este PR funciona directamente sobre `main`: las categorías de los estados incorporados por SIAM-21/25/26 aparecen con cero piezas hasta que existan esos datos. No incluye acciones de baja, robo/extravío ni préstamo. El nuevo campo de colección es opcional; las piezas existentes mantienen sus datos y se agrupan como «Sin colección asignada».

Si `total` es cero, la interfaz muestra «No hay piezas para los filtros seleccionados» (y su traducción al inglés). El reporte consolidado debe consumir estos valores sin recalcular las categorías para que ambos reportes coincidan.
