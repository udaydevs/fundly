import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from django.db import transaction
from ..models import Transaction

REQUIRED_COLUMNS = [
    "date",
    "description",
    "amount",
    "type",
    "reference",
]

MAX_CSV_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DESCRIPTION_LENGTH = 5000
MAX_REFERENCE_LENGTH = 100

# Prevent csv module from rejecting reasonably large fields.
csv.field_size_limit(1024 * 1024)


class CsvFormatError(Exception):
    def __init__(self, message, missing_columns=None):
        self.message = message
        self.missing_columns = missing_columns or []
        super().__init__(message)


def decode_csv(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def parse_amount(value: str) -> Decimal:
    value = value.strip()

    if not value:
        raise ValueError("Amount is required")

    # Examples accepted:
    # 100
    # -100
    # +100
    # 1,000
    # -1,000.50
    # 100.25
    if not re.fullmatch(
        r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?",
        value,
    ):
        raise ValueError(f"Invalid amount: {value}")

    try:
        amount = Decimal(value.replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {value}")

    if amount == 0:
        raise ValueError("Amount cannot be zero")

    if abs(amount) >= Decimal("1000000000000"):
        raise ValueError("Amount is too large")

    return amount.quantize(Decimal("0.01"))


def validate_row(row, line_number):
    errors = []

    # -------------------------
    # Date
    # -------------------------
    date_value = row["date"].strip()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
        errors.append("Date must be in YYYY-MM-DD format")
        transaction_date = None
    else:
        try:
            transaction_date = date.fromisoformat(date_value)
        except ValueError:
            errors.append("Date must be a valid YYYY-MM-DD date")
            transaction_date = None

    # -------------------------
    # Description
    # -------------------------
    description = row["description"].strip()

    if not description:
        errors.append("Description is required")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters"
        )

    # -------------------------
    # Amount
    # -------------------------
    try:
        amount = parse_amount(row["amount"])
    except ValueError as error:
        amount = None
        errors.append(str(error))

    # -------------------------
    # Type
    # -------------------------
    transaction_type = row["type"].strip().lower()

    if transaction_type not in {
        "credit",
        "debit",
    }:
        errors.append("Type must be credit or debit")

    # Credit must be positive
    # Debit must be negative
    if amount is not None:
        if transaction_type == "credit" and amount <= 0:
            errors.append("Credit amount must be positive")

        elif transaction_type == "debit" and amount >= 0:
            errors.append("Debit amount must be negative")

    # -------------------------
    # Reference
    # -------------------------
    reference = row["reference"].strip()

    if not reference:
        errors.append("Reference is required")
    elif len(reference) > MAX_REFERENCE_LENGTH:
        errors.append(
            f"Reference cannot exceed {MAX_REFERENCE_LENGTH} characters"
        )

    if errors:
        return None, {
            "line": line_number,
            "message": "; ".join(errors),
        }

    return {
        "date": transaction_date,
        "description": description,
        "amount": amount,
        "type": transaction_type,
        "reference": reference,
        "line": line_number,
    }, None


def parse_csv(data: bytes):
    # -------------------------
    # File size check
    # -------------------------
    if not data:
        raise CsvFormatError(
            "CSV file is empty",
            REQUIRED_COLUMNS,
        )

    if len(data) > MAX_CSV_SIZE:
        raise CsvFormatError(
            "CSV file cannot exceed 10 MB",
        )

    # -------------------------
    # Decode
    # -------------------------
    text = decode_csv(data)

    if not text.strip():
        raise CsvFormatError(
            "CSV file is empty",
            REQUIRED_COLUMNS,
        )

    reader = csv.reader(io.StringIO(text))

    # -------------------------
    # Header
    # -------------------------
    header = next(reader, None)

    if not header:
        raise CsvFormatError(
            "CSV file is empty",
            REQUIRED_COLUMNS,
        )

    columns = [column.strip().lower() for column in header]

    if not any(columns):
        raise CsvFormatError(
            "CSV header is empty",
            REQUIRED_COLUMNS,
        )

    # -------------------------
    # Duplicate columns
    # -------------------------
    duplicates = {
        column
        for column in columns
        if column and columns.count(column) > 1
    }

    if duplicates:
        raise CsvFormatError(
            f"Duplicate columns: {', '.join(sorted(duplicates))}"
        )

    # -------------------------
    # Required columns
    # -------------------------
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in columns
    ]

    if missing:
        raise CsvFormatError(
            f"Missing columns: {', '.join(missing)}",
            missing,
        )

    # -------------------------
    # Column indexes
    # -------------------------
    indexes = {
        column: columns.index(column)
        for column in REQUIRED_COLUMNS
    }

    valid_rows = []
    errors = []

    # -------------------------
    # Rows
    # -------------------------
    for line_number, record in enumerate(reader, start=2):

        # Ignore completely empty rows
        if not record or not any(cell.strip() for cell in record):
            continue

        # Every row must have exactly the same
        # number of columns as the header.
        if len(record) != len(columns):
            errors.append({
                "line": line_number,
                "message": (
                    f"Expected {len(columns)} columns, "
                    f"got {len(record)}"
                ),
            })
            continue

        row_data = {
            column: record[index].strip()
            for column, index in indexes.items()
        }

        valid_row, error = validate_row(
            row_data,
            line_number,
        )

        if error:
            errors.append(error)
        else:
            valid_rows.append(valid_row)

    return valid_rows, errors
def import_statement(organization, data):
    rows, errors = parse_csv(data)

    if errors:
        return {
            "imported": 0,
            "errors": errors,
        }

    imported = 0

    with transaction.atomic():
        for row in rows:
            Transaction.objects.create(
                org=organization,
                date=row["date"],
                descp=row["description"],
                amt=row["amount"],
                type=row["type"],
                bank_ref=row["reference"],
                status=Transaction.Status.NEEDS_REVIEW,
            )
            imported += 1

    return {
        "imported": imported,
        "errors": [],
    }