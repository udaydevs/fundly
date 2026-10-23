"""Authentication permission"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import ValidationError, NotFound

from .models import Organization

class OrganizationHeaderPerm(BasePermission):
    """This will check the existence of the organization
    from the X-Organization header and attach it to the request"""

    def has_permission(self, request,view):
        """This will check if the header exist or not"""
        slug = request.headers.get("X-Organization")
        if not slug:
            raise ValidationError({
                'err' : 'Missing Request Header',
                }
            )
        try:
            request.organization = Organization.objects.get(slug = slug)
        except Organization.DoesNotExist:
            raise NotFound({
                'err': "Organization does not exist",
            })
        return True
