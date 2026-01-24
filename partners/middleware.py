from django.conf import settings


class PartnerSessionMiddleware:
    """
    Middleware that uses a separate session cookie for /partners/ URLs.

    This allows admin and partner users to be logged in simultaneously
    without interfering with each other's sessions.
    """

    PARTNERS_SESSION_COOKIE = "partners_sessionid"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # For /partners/ URLs, swap the session cookie name before processing
        if request.path.startswith("/partners/"):
            original_cookie_name = settings.SESSION_COOKIE_NAME
            settings.SESSION_COOKIE_NAME = self.PARTNERS_SESSION_COOKIE

            response = self.get_response(request)

            # Restore original cookie name
            settings.SESSION_COOKIE_NAME = original_cookie_name
            return response

        return self.get_response(request)
