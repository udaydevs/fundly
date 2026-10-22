import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from ..models import Transaction, LineItem, Match, Organization
from .matching import Candidate, find_matches


REQUIRED_COLUMNS = ["date", "description", "amount", "type", "reference"]


class CsvFormatError(Exception):
    def __init__(self, message, missing_columns=None):
        self.message = message
        self.missing_columns = missing_columns or []
        super().__init__(message)


def decode_csv(data):
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")

def parse_amount(value):
    value = value.strip()
    if not value:
        raise ValueError("Amount is required")
    if not re.fullmatch(r"[+-]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?", value):
        raise ValueError(f"Invalid amount: {value}")
    try:
        amount = Decimal(value.replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {value}")
    if amount == 0:
        raise ValueError("Amount cannot be zero")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("Amount can have at most 2 decimal places")
    if abs(amount) >= Decimal("1000000000000"):
        raise ValueError("Amount is too large")
    return amount.quantize(Decimal("0.01"))

def validate_row(row, line_number):
    errors = []
    try:
        transaction_date = date.fromisoformat(row["date"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            raise ValueError
    except ValueError:
        transaction_date = None
        errors.append("Date must be a valid YYYY-MM-DD date")
    description = row["description"]
    if not description:
        errors.append("Description is required")
    try:
        amount = parse_amount(row["amount"])
    except ValueError as error:
        amount = None
        errors.append(str(error))
    transaction_type = row["type"].lower()
    if transaction_type not in ["credit", "debit"]:
        errors.append("Type must be credit or debit")
    if amount is not None:
        if transaction_type == "credit" and amount < 0:
            errors.append("Credit amount must be positive")
        elif transaction_type == "debit" and amount > 0:
            errors.append("Debit amount must be negative")
    reference = row["reference"]
    if not reference:
        errors.append("Reference is required")
    elif len(reference) > 100:
        errors.append("Reference cannot exceed 100 characters")
    if errors:
        return None, {
            "line": line_number,
            "message": "; ".join(errors)
        }
    return {
        "date": transaction_date,
        "description": description,
        "amount": amount,
        "type": transaction_type,
        "reference": reference,
        "line": line_number,
    }, None

def parse_csv(data):
    text = decode_csv(data)
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header or not any(column.strip() for column in header):
        raise CsvFormatError("CSV file is empty", REQUIRED_COLUMNS)
    columns = [column.strip().lower() for column in header]
    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in columns
    ]
    if missing:
        raise CsvFormatError(
            f"Missing columns: {', '.join(missing)}",
            missing
        )
    indexes = {
        column: columns.index(column)
        for column in REQUIRED_COLUMNS
    }
    valid_rows = []
    errors = []
    for line_number, record in enumerate(reader, start=2):
        if not any(cell.strip() for cell in record):
            continue
        if len(record) != len(columns):
            errors.append({
                "line": line_number,
                "message": "Incorrect number of columns"
            })
            continue
        row_data = {
            column: record[index].strip()
            for column, index in indexes.items()
        }
        valid_row, error = validate_row(row_data, line_number)
        if error:
            errors.append(error)
        else:
            valid_rows.append(valid_row)
    return valid_rows, errors

def get_candidates(organization):
    line_items = (
        LineItem.objects
        .filter(organization=organization)
        .select_related("capital_call")
        .order_by("capital_call__call_date", "id")
    )
    candidates = []
    for item in line_items:
        if item.amount_remaining > 0:
            candidates.append(
                Candidate.build(
                    item.id,
                    item.reference,
                    item.investor_name,
                    item.capital_call.call_date,
                    item.amount_remaining,
                )
            )
    return candidates

def import_statement(organization: Organization, data: bytes):
    rows, errors = parse_csv(data)
    imported_transactions = []
    duplicate_details = []
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=organization.pk)
        existing_references = set(
            Transaction.objects
            .filter(organization=organization)
            .values_list("bank_reference", flat=True)
        )
        candidates = get_candidates(organization)
        seen_references = set()
        for row in rows:
            reference = row["reference"]
            if reference in existing_references or reference in seen_references:
                duplicate_details.append({
                    "line": row["line"],
                    "reference": reference,
                })
                continue
            seen_references.add(reference)
            transaction_obj = Transaction(
                organization=organization,
                date=row["date"],
                description=row["description"],
                amount=row["amount"],
                type=row["type"],
                bank_reference=reference,
                source_line=row["line"],
            )
            if row["type"] == Transaction.Type.DEBIT:
                transaction_obj.status = Transaction.Status.IGNORED
                transaction_obj.reason = (
                    "Debit (money out) cannot pay a capital call"
                )
                outcome = None
            else:
                outcome = find_matches(
                    row["date"],
                    row["amount"],
                    row["description"],
                    reference,
                    candidates,
                )
                transaction_obj.status = outcome.status
                transaction_obj.reason = outcome.reason
            imported_transactions.append((transaction_obj, outcome))
        Transaction.objects.bulk_create(
            [item[0] for item in imported_transactions],
            batch_size=500,
        )
        matches = []
        for transaction_obj, outcome in imported_transactions:
            if not outcome:
                continue
            for proposal in outcome.proposals:
                matches.append(
                    Match(
                        organization=organization,
                        transaction=transaction_obj,
                        line_item_id=proposal.line_item_id,
                        status=Match.Status.PROPOSED,
                        reason=proposal.reason,
                    )
                )
        Match.objects.bulk_create(matches, batch_size=500)
    breakdown = {
        status.value: 0
        for status in Transaction.Status
    }
    for transaction_obj, _ in imported_transactions:
        breakdown[transaction_obj.status] += 1
    return {
        "imported": len(imported_transactions),
        "duplicates": len(duplicate_details),
        "duplicate_details": duplicate_details,
        "errors": errors,
        "breakdown": breakdown,
    }
