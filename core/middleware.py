import hashlib
from django.db.models import F
from django.utils import timezone
from .models import VisitorCount


class VisitorCountMiddleware:
    """Count unique visits using a daily cookie.
    Same visitor is counted only once per day.
    Uses atomic DB F() increment to prevent race conditions under concurrent requests.
    """

    SKIP_PREFIXES = (
        '/admin/', '/dashboard/', '/static/', '/media/',
        '/ckeditor5/', '/robots.txt', '/favicon.ico',
        '/sitemap.xml', '/ads.txt',
    )
    COOKIE_NAME = 'vc_counted'

    def __init__(self, get_response):
        self.get_response = get_response

    def _should_skip(self, path):
        return any(path.startswith(p) for p in self.SKIP_PREFIXES)

    def __call__(self, request):
        path = request.path
        today_str = timezone.now().strftime('%Y%m%d')
        should_set_cookie = False

        if not self._should_skip(path):
            if request.COOKIES.get(self.COOKIE_NAME) != today_str:
                # Atomic increment — safe under concurrent requests
                updated = VisitorCount.objects.filter(pk=1).update(count=F('count') + 1)
                if updated == 0:
                    # No record yet — create with count=1
                    VisitorCount.objects.get_or_create(pk=1, defaults={'count': 1})
                should_set_cookie = True

        response = self.get_response(request)

        # Set the daily cookie so the same visitor isn't counted again today
        if should_set_cookie:
            response.set_cookie(
                self.COOKIE_NAME,
                today_str,
                max_age=86400,   # Expires after 1 day
                httponly=True,
                samesite='Lax',
            )

        return response