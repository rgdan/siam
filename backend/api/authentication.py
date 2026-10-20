from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    def authenticate_header(self, request):
        # DRF convierte los errores de sesión en 403 si no hay este encabezado.
        return "Session"
