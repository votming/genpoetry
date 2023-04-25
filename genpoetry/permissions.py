from rest_framework.permissions import BasePermission

from configuration import Config


class TokenPermission(BasePermission):
    def has_permission(self, request, view):
        token = request.META.get(f'HTTP_AUTHORIZATION', 'empty')
        param_token = request.query_params.get('AUTHORIZATION')
        return token == Config.AUTHORIZATION_TOKEN or param_token == Config.AUTHORIZATION_TOKEN
