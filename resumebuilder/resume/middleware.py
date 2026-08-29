from urllib.parse import urlencode
from django.shortcuts import redirect


class LocalHostRedirectMiddleware:
    """
    Keep local authentication on lvh.me so the shared .lvh.me
    session cookie works consistently for the main site and subdomains.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host in ('127.0.0.1', 'localhost'):
            query = request.META.get('QUERY_STRING', '')
            target = f'http://lvh.me:8000{request.path}'
            if query:
                target += f'?{query}'
            return redirect(target)
        return self.get_response(request)


from django.contrib.auth import logout
from django.contrib.auth.models import User

class SubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # remove port

        parts = host.split('.')

        # Example: john.lvh.me → ['john','lvh','me']
        if len(parts) > 2:
            request.subdomain = parts[0]
        else:
            request.subdomain = None

        return self.get_response(request)
    
class ForceLogoutIfUserDeletedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not User.objects.filter(id=request.user.id).exists():
                logout(request)
        return self.get_response(request)