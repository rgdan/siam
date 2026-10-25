<div align="center">

# SIAM

Sistema de Información y Analítica Museal

**Vue.js + Vite · Django REST Framework · SQLite**

Proyecto del curso Requerimientos del Software · Tecnológico de Costa Rica

</div>

---

Sistema en desarrollo para apoyar la gestión de visitantes, eventos y colecciones
del Museo Histórico Cultural Juan Santamaría.

## Desarrollo local

El frontend y el backend son independientes y se comunican mediante una API REST en JSON.
Consulte las instrucciones de cada componente y ejecútelos en terminales separadas.

| Componente | Tecnología | Instalación y ejecución |
|---|---|---|
| Interfaz web | Vue.js + Vite | [Frontend](frontend/README.md) |
| API | Python + Django REST Framework | [Backend](backend/README.md) |

Para generar una cuenta de prueba por rol, ejecute `python crear_usuarios_demo.py` desde `backend/`.
Consulte los [correos, contraseña e instrucciones](backend/README.md#cuentas-de-prueba). Solo para desarrollo local.
