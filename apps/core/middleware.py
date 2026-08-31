import logging
import time
import uuid

from django.conf import settings
from django.utils.cache import patch_cache_control

monitoring_logger = logging.getLogger("vivabem.monitoring")


class RequestMonitoringMiddleware:
    """Add a trace identifier and log failures/slow requests without user data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        started_at = time.monotonic()

        try:
            response = self.get_response(request)
        except Exception:
            monitoring_logger.exception(
                "Falha não tratada method=%s path=%s request_id=%s",
                request.method,
                request.path,
                request_id,
            )
            raise

        elapsed_ms = round((time.monotonic() - started_at) * 1000)
        response["X-Request-ID"] = request_id

        if response.status_code >= 500:
            monitoring_logger.error(
                "Resposta com erro method=%s path=%s status=%s duration_ms=%s request_id=%s",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
                request_id,
            )
        elif elapsed_ms >= settings.VIVABEM_SLOW_REQUEST_MS:
            monitoring_logger.warning(
                "Resposta lenta method=%s path=%s status=%s duration_ms=%s request_id=%s",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
                request_id,
            )

        return response


class VivaBemSecurityHeadersMiddleware:
    """Add privacy-focused headers without changing application responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        if request.user.is_authenticated:
            patch_cache_control(
                response,
                private=True,
                no_cache=True,
                no_store=True,
                must_revalidate=True,
            )
        return response
