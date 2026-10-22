"""All the views are here."""
from rest_framework.response import Response
from rest_framework.views import APIView

class OrganizationView(APIView):
    """
    Organization view contains the get request which will 
    check if the organization exist or not.
    """
    def get(self, request):
        """Get Organization from the request and return org details"""
        org = request.organization
        return Response({"slug": org.slug, "name": org.name})
