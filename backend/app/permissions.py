"""Authentication permission"""
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from .models import Organization

class OrganizationHeaderPerm(BasePermission):
    """This will check the existence of the organization
    from the X-Organization header and attach it to the request"""

    def has_permission(self, request):
        """This will check if the header exist or not"""
        slug = request.headers.get("X-Organization")
        if not slug:
            return Response({
                'err' : 'Missing Request Header'
                },
                status = status.HTTP_400_BAD_REQUEST
            )
        try:
            request.organization = Organization.object.get(slug = slug)
        except Organization.DoesNotExist:
            return Response({
                'err' : 'Organization does not exist'
                },
                status = status.HTTP_400_BAD_REQUEST
            )
        return True
