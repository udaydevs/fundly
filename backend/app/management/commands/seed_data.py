from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import CapitalCall, LineItem, Organization

ORGANIZATIONS = [("northwind", "Northwind Ventures"), ("bluebird", "Bluebird Capital")]

# (org slug, call number, call date, due date)
CALLS = [
    ("northwind", 1, date(2026, 3, 25), date(2026, 4, 10)),
    ("northwind", 2, date(2026, 4, 1), date(2026, 4, 20)),
    ("bluebird", 1, date(2026, 4, 1), date(2026, 4, 15)),
]

LINE_ITEMS = [
    ("northwind", 1, "Haller Capital LLC", "CC-1001", "27500.00"),
    ("northwind", 1, "Rahul Shah Trust", "CC-1002", "25000.00"),
    ("northwind", 1, "Patel Family Trust", "CC-1003", "12500.00"),
    ("northwind", 1, "Meridian Partners LP", "CC-1004", "15000.00"),
    ("northwind", 1, "Oakridge Holdings LLC", "CC-1005", "15000.00"),
    ("northwind", 2, "Oakridge Holdings LLC", "CC-1006", "15000.00"),
    ("bluebird", 1, "Cedar Grove Fund LP", "CC-2001", "40000.00"),
]


class Command(BaseCommand):
    help = "Create the demo organizations, capital calls and line items. Safe to run repeatedly."

    @transaction.atomic
    def handle(self, *args, **options):
        orgs = {}
        for slug, name in ORGANIZATIONS:
            orgs[slug], _ = Organization.objects.update_or_create(slug=slug, defaults={"org_name": name})

        calls = {}
        for slug, number, call_date, due_date in CALLS:
            calls[(slug, number)], _ = CapitalCall.objects.update_or_create(
                org=orgs[slug], number=number, defaults={"call_date": call_date, "due_date": due_date}
            )

        created = 0
        for slug, number, investor, reference, amount in LINE_ITEMS:
            # get_or_create: never reset amounts already funded by approved matches.
            _, was_created = LineItem.objects.get_or_create(
                org=orgs[slug],
                ref=reference,
                defaults={
                    "cap_call": calls[(slug, number)],
                    "investor": investor,
                    "called_amt": Decimal(amount),
                    "funded_amt": Decimal("0.00"),
                    "status": LineItem.Status.OPEN,
                },
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created} new line item(s), {len(LINE_ITEMS)} total."))
