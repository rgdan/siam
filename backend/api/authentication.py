from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    # Permite responder 401 sin sesión; DRF usaría 403 si faltara este encabezado.
    def authenticate_header(self, request):
        return "Session"
