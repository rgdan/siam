from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication
from drf_spectacular.authentication import SessionScheme


class SessionAuthentication(DRFSessionAuthentication):
    # Permite responder 401 sin sesión; DRF usaría 403 si faltara este encabezado.
    def authenticate_header(self, request):
        return "Session"


class SIAMSessionScheme(SessionScheme):
    target_class = "api.authentication.SessionAuthentication"
