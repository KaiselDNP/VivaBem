import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def env_int(name, default):
    value = os.getenv(name)
    try:
        return int(value) if value is not None else default
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} precisa ser um número inteiro.") from exc


DEBUG = env_bool("VIVABEM_DEBUG", True)
SECRET_KEY = os.getenv("VIVABEM_DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina VIVABEM_DJANGO_SECRET_KEY no ambiente.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("VIVABEM_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("VIVABEM_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts.apps.AccountsConfig",
    "apps.profiles.apps.ProfilesConfig",
    "apps.professionals.apps.ProfessionalsConfig",
    "apps.needs.apps.NeedsConfig",
    "apps.relationships.apps.RelationshipsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.chat.apps.ChatConfig",
    "apps.moderation.apps.ModerationConfig",
    "apps.core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.RequestMonitoringMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.UserActivityMiddleware",
    "apps.core.middleware.VivaBemSecurityHeadersMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.notifications.context_processors.notification_counts",
                "apps.chat.context_processors.unread_chat_messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

database_url = os.getenv("DATABASE_URL", "").strip()
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("VIVABEM_DB_NAME", "vivabem"),
            "USER": os.getenv("VIVABEM_DB_USER", "vivabem_app"),
            "PASSWORD": os.getenv("VIVABEM_DB_PASSWORD"),
            "HOST": os.getenv("VIVABEM_DB_HOST", "localhost"),
            "PORT": os.getenv("VIVABEM_DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "TEST": {"NAME": os.getenv("VIVABEM_DB_TEST_NAME", "vivabem_test")},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
media_root = os.getenv("VIVABEM_MEDIA_ROOT", "").strip()
MEDIA_ROOT = Path(media_root) if media_root else BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

EMAIL_BACKEND = os.getenv(
    "VIVABEM_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.getenv("VIVABEM_DEFAULT_FROM_EMAIL", "VivaBem <nao-responda@vivabem.local>")
EMAIL_HOST = os.getenv("VIVABEM_EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("VIVABEM_EMAIL_PORT", 587)
EMAIL_HOST_USER = os.getenv("VIVABEM_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("VIVABEM_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("VIVABEM_EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("VIVABEM_EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("VIVABEM_EMAIL_TIMEOUT", 10)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured(
        "Ative apenas uma opção entre VIVABEM_EMAIL_USE_TLS e VIVABEM_EMAIL_USE_SSL."
    )

LOGIN_MAX_ATTEMPTS = env_int("VIVABEM_LOGIN_MAX_ATTEMPTS", 5)
LOGIN_LOCKOUT_SECONDS = env_int("VIVABEM_LOGIN_LOCKOUT_SECONDS", 600)
PASSWORD_RESET_TIMEOUT = env_int("VIVABEM_PASSWORD_RESET_TIMEOUT", 3600)
USER_ACTIVITY_UPDATE_SECONDS = env_int("VIVABEM_ACTIVITY_UPDATE_SECONDS", 120)
USER_ONLINE_WINDOW_SECONDS = env_int("VIVABEM_ONLINE_WINDOW_SECONDS", 300)
VIVABEM_SLOW_REQUEST_MS = env_int("VIVABEM_SLOW_REQUEST_MS", 1500)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = env_int("VIVABEM_SESSION_COOKIE_AGE", 14400)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = env_bool("VIVABEM_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = env_int(
    "VIVABEM_SECURE_HSTS_SECONDS",
    0 if DEBUG else 31536000,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("VIVABEM_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("VIVABEM_SECURE_HSTS_PRELOAD", False)
if env_bool("VIVABEM_BEHIND_HTTPS_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "concise": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "concise",
        },
    },
    "loggers": {
        "vivabem.monitoring": {
            "handlers": ["console"],
            "level": os.getenv("VIVABEM_LOG_LEVEL", "INFO").upper(),
            "propagate": False,
        },
    },
}
