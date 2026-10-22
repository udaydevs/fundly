from django.db import transaction
from django.db.models import F

from ..models import Transaction, LineItem, Match
from .matching import money

OPEN_STATUSES = (Transaction.Status.SUGGESTED, Transaction.Status.NEEDS_REVIEW)


def _lock_match_and_transaction(organization, match_id):
    owner = Match.objects.filter(pk=match_id, organization=organization).values_list("transaction_id", flat=True).first()
    if owner is None:
        raise Exception("Match not found")
    tx = Transaction.objects.select_for_update().get(pk=owner)
    match = Match.objects.select_for_update().get(pk=match_id)
    return tx, match


@transaction.atomic
def approve_match(organization, match_id) -> Transaction:
    tx, match = _lock_match_and_transaction(organization, match_id)

    if tx.status not in OPEN_STATUSES:
        raise Exception(f"Transaction is already {tx.status}")
    if match.status != Match.Status.PROPOSED:
        raise Exception(f"Match is already {match.status}")
    if tx.type != Transaction.Type.CREDIT:
        raise Exception("Only credits can pay a capital call")

    line = LineItem.objects.select_for_update().get(pk=match.line_item_id)
    if tx.amount > line.amount_remaining:
        raise Exception(
            f"Amount {money(tx.amount)} is more than the remaining {money(line.amount_remaining)} on {line.reference}"
        )

    updated = LineItem.objects.filter(pk=line.pk, amount_funded__lte=F("amount_called") - tx.amount).update(
        amount_funded=F("amount_funded") + tx.amount
    )
    if updated != 1:
        raise Exception(f"Line item {line.reference} can no longer take this amount")
    line.refresh_from_db()
    line.status = line.compute_status()
    line.save(update_fields=["status"])

    match.status = Match.Status.APPROVED
    match.save(update_fields=["status"])
    tx.matches.exclude(pk=match.pk).filter(status=Match.Status.PROPOSED).update(status=Match.Status.REJECTED)

    tx.status = Transaction.Status.RECONCILED
    tx.reason = f"Reconciled to {line.reference} ({line.investor_name}): {match.reason}"
    tx.save(update_fields=["status", "reason"])
    return tx


@transaction.atomic
def reject_match(organization, match_id) -> Transaction:
    tx, match = _lock_match_and_transaction(organization, match_id)

    if tx.status not in OPEN_STATUSES:
        raise Exception(f"Transaction is already {tx.status}")
    if match.status != Match.Status.PROPOSED:
        raise Exception(f"Match is already {match.status}")

    match.status = Match.Status.REJECTED
    match.save(update_fields=["status"])

    if not tx.matches.filter(status=Match.Status.PROPOSED).exists():
        tx.status = Transaction.Status.NEEDS_REVIEW
        tx.reason = "All proposed matches were rejected; no line item selected"
        tx.save(update_fields=["status", "reason"])
    return tx


@transaction.atomic
def ignore_transaction(organization, transaction_id) -> Transaction:
    if not Transaction.objects.filter(pk=transaction_id, organization=organization).exists():
        raise Exception("Transaction not found")
    tx = Transaction.objects.select_for_update().get(pk=transaction_id)

    if tx.status == Transaction.Status.RECONCILED:
        raise Exception("A reconciled transaction cannot be ignored")
    if tx.status not in OPEN_STATUSES:
        raise Exception(f"Transaction is already {tx.status}")

    tx.matches.filter(status=Match.Status.PROPOSED).update(status=Match.Status.REJECTED)
    tx.status = Transaction.Status.IGNORED
    tx.reason = "Ignored by the GP"
    tx.save(update_fields=["status", "reason"])
    return tx
