"""All the views are here."""

from django.conf import settings
from django.db.models import Count, Prefetch

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LineItem, Match, Transaction
from .serializers import LineItemSerializer, TransactionSerializer
from .services import check_csv, reconciliation


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"


def run_reconciliation(function, organization, pk):
    try:
        return function(organization, pk)
    except Exception as error:
        raise APIException(str(error))


def get_transactions(organization):
    return (
        Transaction.objects
        .filter(org=organization)
        .prefetch_related(
            Prefetch(
                "matches",
                queryset=Match.objects.select_related(
                    "line_item__cap_call"
                ).order_by("id"),
            )
        )
    )


class OrganizationView(APIView):
    def get(self, request):
        org = request.organization

        return Response({
            "slug": org.slug,
            "name": org.org_name,
        })


class TransactionView(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        org = self.request.organization

        return (
            Transaction.objects
            .filter(org=org)
            .order_by("-date", "-id")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            transactions = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            transactions = serializer.data

        counts = (
            Transaction.objects
            .filter(org=request.organization)
            .values("status")
            .annotate(total=Count("id"))
        )

        status_counts = {
            item["status"]: item["total"]
            for item in counts
        }

        for transaction_status in Transaction.Status.values:
            status_counts.setdefault(transaction_status, 0)

        return Response({
            "transactions": transactions,
            "status_counts": status_counts,
        })

    @action(
        detail=False,
        methods=["post"],
        url_path="import",
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def import_csv(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {
                    "detail": (
                        "Please upload a CSV file using the 'file' field."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_import_bytes = getattr(
            settings,
            "MAX_IMPORT_BYTES",
            10 * 1024 * 1024,
        )

        if uploaded_file.size > max_import_bytes:
            return Response(
                {"detail": "File is too large."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not uploaded_file.name.lower().endswith(".csv"):
            return Response(
                {"detail": "Only CSV files are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = check_csv.import_statement(
                request.organization,
                uploaded_file.read(),
            )

        except check_csv.CsvFormatError as error:
            return Response(
                {
                    "detail": error.message,
                    "missing_columns": error.missing_columns,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def ignore(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.ignore_transaction,
            request.organization,
            pk,
        )

        transaction = get_transactions(
            request.organization
        ).get(pk=transaction.pk)

        return Response(
            TransactionSerializer(transaction).data
        )


class MatchViewSet(viewsets.GenericViewSet):
    """Approve or reject proposed transaction matches."""

    def get_queryset(self):
        return Match.objects.filter(
            organization=self.request.organization
        )

    def respond(self, request, transaction):
        transaction = get_transactions(
            request.organization
        ).get(pk=transaction.pk)

        return Response(
            TransactionSerializer(transaction).data
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.approve_match,
            request.organization,
            pk,
        )

        return self.respond(request, transaction)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        transaction = run_reconciliation(
            reconciliation.reject_match,
            request.organization,
            pk,
        )

        return self.respond(request, transaction)


class LineItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LineItemSerializer
    pagination_class = None

    def get_queryset(self):
        line_items = (
            LineItem.objects
            .filter(org=self.request.organization)
            .select_related("cap_call")
        )

        status_filter = self.request.query_params.get("status")

        if status_filter:
            if status_filter not in LineItem.Status.values:
                raise ValidationError({
                    "status": (
                        "Invalid status. Choose from: "
                        + ", ".join(LineItem.Status.values)
                    )
                })

            line_items = line_items.filter(
                status=status_filter
            )

        return line_items.order_by(
            "cap_call__number",
            "id",
        )
