from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

from .models import ExpiredTokenProxy


class TokenNotExpiredAuth(TokenAuthentication):
    model = ExpiredTokenProxy

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if token.is_expired:
            raise exceptions.AuthenticationFailed(_("Token is expired."))
        return (user, token)