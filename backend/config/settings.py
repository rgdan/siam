import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "api",
    "audit",
    "collection_integrity",
    "system_configuration",
    "visitors",
    "incidents",
]
AUTH_USER_MODEL = "api.User"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
APPEND_SLASH = False
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_HTTPONLY = True
CSRF_FAILURE_VIEW = "api.views.csrf_failure"

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
}]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),

        "OPTIONS": {"transaction_mode": "IMMEDIATE"},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Costa_Rica"
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["api.authentication.SessionAuthentication"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SIAM API",
    "DESCRIPTION": (
        "Museum Information and Analytics System · Museo Histórico Cultural Juan Santamaría.\n\n"
        "JSON API with session-cookie authentication and role permissions. "
        "Dates use America/Costa_Rica; date filters are inclusive.\n\n"
        "To test locally: execute GET /api/auth/csrf/, then POST /api/auth/login/. "
        "The browser stores the session cookie; Swagger sends the current CSRF cookie "
        "as X-CSRFToken for writes. Do not enter a cookie in the Authorize dialog. "
        "GET /api/auth/me/ returns the account and its permissions. "
        "Login rotates the CSRF token. Errors are JSON detail messages or field errors."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_AUTHENTICATION": [],
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "PieceStateEnum": "api.schema.PIECE_STATES",
        "MissingStateEnum": ["stolen", "lost"],
        "CollectionReportStateEnum": "collection_integrity.reports.REPORT_STATES",
    },
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.34.1",
    "SWAGGER_UI_FAVICON_HREF": None,
    "SWAGGER_UI_SETTINGS": """{
        deepLinking: true,
        docExpansion: 'none',
        displayRequestDuration: true,
        validatorUrl: null,
        requestInterceptor: (request) => {
            if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) {
                const token = document.cookie.split('; ').find(c => c.startsWith('csrftoken='));
                if (token) request.headers['X-CSRFToken'] = decodeURIComponent(token.slice(10));
            }
            return request;
        }
    }""",
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 145 * 1024 * 1024
