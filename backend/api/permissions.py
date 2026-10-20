from rest_framework.decorators import permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated

from .models import User


# Las consultas públicas no requieren sesión; todos los roles internos también las incluyen.
PERMISOS_PUBLICOS = frozenset({"museo.ver_informacion", "eventos.ver_publicos"})
PERMISOS_COMUNES = PERMISOS_PUBLICOS | {"eventos.ver_privados"}

PERMISOS_POR_ROL = {
    User.Role.GUARDA: PERMISOS_COMUNES | {
        "visitantes.registrar",
        "incidencias.registrar",
    },
    User.Role.COORDINADOR: PERMISOS_COMUNES | {
        "eventos.crear",
        "eventos.actualizar",
        "eventos.cancelar",
        "eventos.registrar_asistencia",
        "eventos.generar_reportes",
    },
    User.Role.MUSEOLOGO: PERMISOS_COMUNES | {
        "piezas.crear",
        "piezas.adjuntar_fotos",
        "piezas.actualizar",
        "piezas.dar_baja",
        "piezas.cambiar_exhibicion",
        "piezas.registrar_ubicacion",
        "colecciones.generar_reportes",
        "piezas.registrar_prestamo",
        "piezas.marcar_robo_extravio",
    },
}

# Los administradores heredan permisos, pero cada cuenta sigue teniendo un solo rol.
PERMISOS_POR_ROL[User.Role.ADMINISTRADOR_GENERAL] = (
    PERMISOS_POR_ROL[User.Role.GUARDA]
    | PERMISOS_POR_ROL[User.Role.COORDINADOR]
    | PERMISOS_POR_ROL[User.Role.MUSEOLOGO]
    | {"reportes.ver_consolidados", "operacion.supervisar", "reportes.exportar"}
)
PERMISOS_POR_ROL[User.Role.ADMINISTRADOR_SISTEMA] = (
    PERMISOS_POR_ROL[User.Role.ADMINISTRADOR_GENERAL]
    | {
        "usuarios.consultar",
        "usuarios.crear",
        "usuarios.actualizar",
        "usuarios.eliminar",
        "usuarios.asignar_rol",
        "sistema.configurar",
        "bitacora.consultar",
    }
)


# Solo las cuentas activas con un rol conocido reciben permisos internos.
def permisos_para(user):
    if not user or not user.is_authenticated or not user.is_active:
        return frozenset()
    return PERMISOS_POR_ROL.get(user.role, frozenset())


# Acepta un permiso común o uno por método HTTP; DRF comprueba la sesión primero.
def requiere_permiso(permiso):
    # El permiso queda asociado a esta vista, no al cuerpo de la solicitud del navegador.
    class PermisoRequerido(BasePermission):
        message = "Acceso denegado."

        # Un permiso desconocido tampoco pertenece al conjunto y queda denegado.
        def has_permission(self, request, view):
            requerido = permiso.get(request.method) if isinstance(permiso, dict) else permiso
            return requerido in permisos_para(request.user)

    return permission_classes([IsAuthenticated, PermisoRequerido])
