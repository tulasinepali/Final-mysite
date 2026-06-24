from .models import VisitorCount


class VisitorCountMiddleware:
    """Count unique visits based on session. Each session counts as one visit."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip admin, dashboard, and static/media requests
        path = request.path
        skip_prefixes = ('/admin/', '/dashboard/', '/static/', '/media/', '/ckeditor5/', '/robots.txt', '/favicon.ico')
        if not any(path.startswith(prefix) for prefix in skip_prefixes):
            # Check if this session has already been counted
            if not request.session.get('visit_counted', False):
                VisitorCount.increment()
                request.session['visit_counted'] = True

        response = self.get_response(request)
        return response