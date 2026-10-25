# Verificación de SIAM-33, SIAM-36 y SIAM-32

Ejecutada el 25 de octubre de 2026 sobre Windows, Django 5.2.18, DRF 3.17.2 y SQLite.

| Comprobación | Resultado |
| --- | --- |
| `python backend/manage.py test tests --verbosity 1` | 20 pruebas, OK |
| `python backend/manage.py makemigrations --check --dry-run` | Sin cambios pendientes |
| `python backend/tests/crash_probe.py` | PASS |
| `npm ci` y `npm run build` en frontend | Compilación correcta |

La suite cubre las cinco operaciones de colección, rollback de fotos/historial/auditoría, bitácora de cuentas y login, exclusión recursiva de contraseñas (incluidas claves en español), consulta por filtros con 50 registros por página, denegación de acceso a otros roles y al público, defaults/restauración, validación por campo y lectura pública del cambio en la siguiente solicitud.

La integración de visitantes y eventos verifica el contrato del helper con un modelo sustituto: esas historias todavía deben conectar sus vistas al helper. La verificación del frontend es de compilación; no se realizó una prueba automatizada en navegador.

## Evidencia de interrupción del servidor

La prueba creó una base temporal, confirmó un agregado, inició un servidor WSGI, esperó un checkpoint dentro de una escritura HTTP sin commit, terminó ese proceso y volvió a iniciarlo sobre la misma base.

```json
{
  "test": "SIAM-36 server kill/restart",
  "result": "PASS",
  "before": {
    "titles": ["committed"],
    "counts": [1, 1, 1, 1],
    "photos": ["intact"]
  },
  "after_restart": {
    "titles": ["committed"],
    "counts": [1, 1, 1, 1],
    "photos": ["intact"]
  },
  "interrupted_rows": 0
}
```

Orden de los conteos: piezas, fotos, historiales y auditorías. La foto confirmada conserva su contenido. No se usa ni modifica la base de desarrollo.

Los pasos de reproducción y límites de integración están en [la entrega](entrega-jorge.md).

Ruff: comprobaciones de sintaxis, imports y errores de Python (`E4,E7,E9,F,I`) correctas sobre los módulos añadidos y los archivos de integración modificados.
