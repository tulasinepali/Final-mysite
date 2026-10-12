import re
from django.db.models import F
from django.utils import timezone
from .models import VisitorCount, VisitorLog


def parse_user_agent(ua_string):
    """Lightweight user-agent parser without external dependencies."""
    if not ua_string:
        return {'device_type': 'Desktop', 'browser': 'Unknown', 'os': 'Unknown', 'is_bot': False}

    ua = ua_string.lower()

    # Detect bot
    bot_patterns = ['bot', 'crawler', 'spider', 'slurp', 'googlebot', 'bingbot', 'yandex', 'duckduckbot', 'lighthouse']
    is_bot = any(b in ua for b in bot_patterns)

    # Detect device
    if 'ipad' in ua or 'tablet' in ua:
        device_type = 'Tablet'
    elif 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        device_type = 'Mobile'
    else:
        device_type = 'Desktop'

    # Detect OS
    if 'windows nt 10.0' in ua:
        os = 'Windows 10/11'
    elif 'windows' in ua:
        os = 'Windows'
    elif 'android' in ua:
        os = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os = 'iOS'
    elif 'macintosh' in ua or 'mac os x' in ua:
        os = 'macOS'
    elif 'linux' in ua:
        os = 'Linux'
    elif 'cros' in ua:
        os = 'ChromeOS'
    else:
        os = 'Other'

    # Detect browser
    if 'edg/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'samsungbrowser' in ua:
        browser = 'Samsung Internet'
    elif 'chrome' in ua and 'safari' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    else:
        browser = 'Other'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os,
        'is_bot': is_bot
    }


def get_client_ip(request):
    """Extract client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class VisitorCountMiddleware:
    """Count unique visits and log detailed visitor analytics.
    Same visitor is counted only once per day for total counter.
    Detailed visitor logs recorded for analytics dashboard.
    """

    SKIP_PREFIXES = (
        '/rishav/', '/admin/', '/dashboard/', '/static/', '/media/',
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
            # 1. Total Daily Visitor Counter
            if request.COOKIES.get(self.COOKIE_NAME) != today_str:
                updated = VisitorCount.objects.filter(pk=1).update(count=F('count') + 1)
                if updated == 0:
                    VisitorCount.objects.get_or_create(pk=1, defaults={'count': 1})
                should_set_cookie = True

            # 2. Detailed Visitor Analytics Log
            try:
                ip = get_client_ip(request)
                ua_str = request.META.get('HTTP_USER_AGENT', '')
                parsed = parse_user_agent(ua_str)
                referrer = request.META.get('HTTP_REFERER', '')
                if referrer and len(referrer) > 490:
                    referrer = referrer[:490]
                
                # Check for country header if forwarded by Cloudflare/Proxy
                country = request.META.get('HTTP_CF_IPCOUNTRY') or request.META.get('GEOIP_COUNTRY_NAME') or 'Nepal'

                session_key = request.session.session_key if hasattr(request, 'session') and request.session else None

                VisitorLog.objects.create(
                    ip_address=ip[:50] if ip else '127.0.0.1',
                    path=path[:490],
                    method=request.method[:10],
                    referrer=referrer if referrer else None,
                    user_agent=ua_str[:1000] if ua_str else '',
                    device_type=parsed['device_type'],
                    browser=parsed['browser'],
                    os=parsed['os'],
                    country=country[:60],
                    session_key=session_key,
                    is_bot=parsed['is_bot'],
                )
            except Exception:
                # Visitor logging should never interrupt request handling
                pass

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


class MaintenanceModeMiddleware:
    """
    Guards the public website when maintenance mode is active.
    - Staff / superusers can always bypass and access the entire site.
    - Whitelisted admin, login, and static/media paths are always accessible.
    - Non-staff visitors receive HTTP 503 Service Unavailable with a polished maintenance page.
    """
    WHITELIST_PREFIXES = (
        '/rishav/',
        '/static/',
        '/media/',
        '/health/',
        '/up/',
        '/robots.txt',
        '/favicon.ico',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # 1. Always allow whitelisted URL prefixes (Admin, Login, Static, Health)
        for prefix in self.WHITELIST_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # 2. Authenticated staff or superusers bypass maintenance unconditionally
        if getattr(request, 'user', None) and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return self.get_response(request)

        # 3. Check SiteSettings maintenance state
        try:
            from core.models import SiteSettings
            from django.shortcuts import render
            settings = SiteSettings.objects.first()

            if settings and settings.maintenance_mode and not settings.maintenance_banner_only:
                response = render(
                    request,
                    'maintenance.html',
                    {
                        'site_settings': settings,
                        'maintenance_message': settings.maintenance_message,
                        'estimated_end': settings.maintenance_estimated_end,
                    },
                    status=503
                )
                response['Retry-After'] = '3600'  # Informs search engines and browsers to retry in 1 hour
                return response
        except Exception:
            # If database table is in migration, fail safe and continue
            pass

        return self.get_response(request)