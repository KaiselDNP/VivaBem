from django.utils.cache import patch_cache_control


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
