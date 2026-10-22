"""All the views are here."""
from re import Match

from django.db.models.aggregates import Count
from django.http.multipartparser import MultiPartParser
from rest_framework.decorators import action
from rest_framework import viewsets, status, mixins
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView, settings
from .serializers import LineItemSerializer, TransactionSerializer
from .services import check_csv, reconciliation
from .models import LineItem, Transaction

class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"


def run_reconciliation(function, organization, pk):
    try:
        return function(organization, pk)
    except Exception as error:
        raise Exception(str(error))
    except Exception as error:
        raise Exception(str(error))

def get_transactions(organization):
    return (
        Transaction.objects
        .filter(organization=organization)
        .prefetch_related(
            Prefetch(
                "matches",
                queryset=Match.objects.select_related(
                    "line_item__capital_call"
                ).order_by("id")
            )
        )
    )


class OrganizationView(APIView):
    """
    Organization view contains the get request which will 
    check if the organization exist or not.
    """
    def get(self, request):
        """Get Organization from the request and return org details"""
        org = request.organization
        return Response({"slug": org.slug, "name": org.name})

class TransactionView(viewsets.ReadOnlyModelViewSet):
    """
    All the data that has been loaded from the csv
    can be fetched from this view
    """
    serializer_class = TransactionSerializer


    def get_queryset(self):
        org = self.request.organization
        return Transaction.objects.filter(org =org).order_by("-date", "-id")
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        counts = (
            Transaction.objects
            .filter(org=request.organization)
            .values("status")
            .annotate(total=Count("id"))
        )
        response.data["status_counts"] = {
            item["status"]: item["total"] for item in counts
        }
        for transaction_status in Transaction.Status.values:
            response.data["status_counts"].setdefault(transaction_status, 0)

        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="import",
        parser_classes=[MultiPartParser]
    )
    def import_csv(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response({
                "err": "Please upload a CSV file using the 'file' field."
            }, status=status.HTTP_404_NOT_FOUND)

        if uploaded_file.size > settings.MAX_IMPORT_BYTES:
            return Response({"err": "File is too large."},status= status.HTTP_400_BAD_REQUEST)

        try:
            result = check_csv.import_statement(
                request.organization,
                uploaded_file.read()
            )
        except check_csv.CsvFormatError as error:
            return Response(
                {
                    "detail": error.message,
                    "missing_columns": error.missing_columns
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def ignore(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.ignore_transaction,
            request.organization,
            pk
        )

        transaction = get_transactions(request.organization).get(
            pk=transaction.pk
        )

        return Response(TransactionSerializer(transaction).data)

class MatchViewSet(viewsets.GenericViewSet):
    """Approve or reject proposed transaction matches."""

    def get_queryset(self):
        return Match.objects.filter(
            organization=self.request.organization
        )

    def respond(self, request, transaction):
        transaction = get_transactions(request.organization).get(
            pk=transaction.pk
        )
        return Response(TransactionSerializer(transaction).data)

    # Approve a match
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.approve_match,
            request.organization,
            pk
        )
        return self.respond(request, transaction)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.reject_match,
            request.organization,
            pk
        )
        return self.respond(request, transaction)


class LineItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = LineItemSerializer
    pagination_class = None

    def get_queryset(self):
        line_items = (
            LineItem.objects
            .filter(organization=self.request.organization)
            .select_related("capital_call")
        )

        status_filter = self.request.query_params.get("status")

        if status_filter:
            if status_filter not in LineItem.Status.values:
                raise ValidationError({
                    "status": "Invalid status. Choose from: "
                    + ", ".join(LineItem.Status.values)
                })

            line_items = line_items.filter(status=status_filter)

        return line_items.order_by("capital_call__number", "id")
