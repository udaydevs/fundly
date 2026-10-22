import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

_NON_ALNUM = re.compile(r"[\W_]+")
_NAME_SUFFIXES = {"LLC", "LP", "LTD", "INC"}

SUGGESTED = "suggested"
NEEDS_REVIEW = "needs_review"


def normalise_reference(value: str) -> str:
    return _NON_ALNUM.sub("", value or "").upper()


def normalise_text(value: str) -> str:
    return _NON_ALNUM.sub(" ", (value or "").upper()).strip()


def normalise_name(value: str) -> str:
    parts = normalise_text(value).split()
    if len(parts) > 1 and parts[-1] in _NAME_SUFFIXES:
        parts.pop()
    return " ".join(parts)


def name_in_text(name_key: str, text_key: str) -> bool:
    return bool(name_key) and f" {name_key} " in f" {text_key} "


def money(value: Decimal) -> str:
    return f"{value:,.2f}"


@dataclass(frozen=True)
class Candidate:

    line_item_id: int
    reference: str
    investor_name: str
    call_date: date
    remaining: Decimal
    ref_key: str
    name_key: str

    @classmethod
    def build(cls, line_item_id, reference, investor_name, call_date, remaining):
        return cls(
            line_item_id=line_item_id,
            reference=reference,
            investor_name=investor_name,
            call_date=call_date,
            remaining=remaining,
            ref_key=normalise_reference(reference),
            name_key=normalise_name(investor_name),
        )


@dataclass
class Proposal:
    line_item_id: int
    reason: str


@dataclass
class MatchOutcome:
    status: str
    reason: str
    proposals: list = field(default_factory=list)


def find_matches(tx_date: date, amount: Decimal, description: str, bank_reference: str, candidates) -> MatchOutcome:
    """Apply the matching rule to one credit and return the status, reason and proposed matches."""
    eligible = [c for c in candidates if c.remaining > 0 and c.call_date <= tx_date]

    desc_key = normalise_reference(description)
    bank_key = normalise_reference(bank_reference)
    ref_hits = [c for c in eligible if c.ref_key and (c.ref_key in desc_key or c.ref_key in bank_key)]

    if len(ref_hits) == 1:
        c = ref_hits[0]
        if amount > c.remaining:
            return MatchOutcome(
                NEEDS_REVIEW,
                f"Reference {c.reference} found, but amount {money(amount)} is more than "
                f"remaining {money(c.remaining)} (overpayment)",
            )
        if amount == c.remaining:
            reason = f"Reference {c.reference} found; amount equals remaining {money(c.remaining)}"
        else:
            reason = (
                f"Reference {c.reference} found; partial payment of {money(amount)} "
                f"against remaining {money(c.remaining)}"
            )
        return MatchOutcome(SUGGESTED, reason, [Proposal(c.line_item_id, reason)])

    if len(ref_hits) > 1:
        proposals = [
            Proposal(
                c.line_item_id,
                f"Reference {c.reference} found; amount {money(amount)} against remaining {money(c.remaining)}",
            )
            for c in ref_hits
        ]
        refs = ", ".join(c.reference for c in ref_hits)
        return MatchOutcome(NEEDS_REVIEW, f"References found for {len(ref_hits)} line items ({refs}); pick one", proposals)

    text_key = normalise_text(description)
    name_hits = [c for c in eligible if c.remaining == amount and name_in_text(c.name_key, text_key)]

    if len(name_hits) == 1:
        c = name_hits[0]
        reason = f"Investor name {c.investor_name} found; amount equals remaining {money(c.remaining)}"
        return MatchOutcome(SUGGESTED, reason, [Proposal(c.line_item_id, reason)])

    if len(name_hits) > 1:
        proposals = [
            Proposal(c.line_item_id, f"Investor name {c.investor_name} found; amount equals remaining {money(c.remaining)}")
            for c in name_hits
        ]
        refs = ", ".join(c.reference for c in name_hits)
        return MatchOutcome(
            NEEDS_REVIEW,
            f"Investor name and amount match {len(name_hits)} line items ({refs}); pick one",
            proposals,
        )

    return MatchOutcome(
        NEEDS_REVIEW,
        "No reference found, and no line item matches both investor name and amount",
    )

