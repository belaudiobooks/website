from django.http import HttpRequest, HttpResponsePermanentRedirect


class WwwRedirectMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        host = request.get_host().partition(":")[0]
        if host.startswith("www."):
            return HttpResponsePermanentRedirect(
                request.get_raw_uri().replace("://www.", "://")
            )
        else:
            return self.get_response(request)
