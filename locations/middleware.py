from django.http import HttpResponseForbidden
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.response import Response

class MediaAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/media/files/'):
            access_token = request.headers.get('Authorization')

            if not access_token or not access_token.startswith('Bearer '):
                return HttpResponseForbidden('Access token is required to access this file.')

            access_token = access_token.split('Bearer ')[1]

            try:
                token = AccessToken.objects.get(token=access_token)
            except AccessToken.DoesNotExist:
                return HttpResponseForbidden('Invalid access token.')

            if token.user == AnonymousUser() or token.expires < timezone.now():
                return HttpResponseForbidden('You do not have permission to access this file.')

        return response
