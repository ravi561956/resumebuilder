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