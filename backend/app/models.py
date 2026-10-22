from django.db import models
from django.db.models import F, Q


class Organization(models.Model):
    org_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)


class CapitalCall(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    call_date = models.DateField()
    number = models.PositiveIntegerField()
    due_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(due_date__gte=F("call_date")),
                name='call_date_should_be_greater_than_due_date'),
        ]

class LineItem(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open'
        PARTIALLY_FUNDED = 'partially_funded'
        FUNDED = 'funded'
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    cap_call = models.ForeignKey(CapitalCall, on_delete=models.CASCADE)
    called_amt  = models.DecimalField(max_digits=14, decimal_places=2)
    investor = models.CharField(max_length=200)
    ref = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    funded_amt =  models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
          constraints = [
            models.CheckConstraint(condition=Q(called_amt__gt=0),
                                   name="called_amt_should_be_positive"),
            models.CheckConstraint(condition=Q(funded_amt__gte=0),
                                   name="funded_amt_should_be_positive"),
            models.CheckConstraint(condition=Q(funded_amt__lte=F("called_amt")),
                                   name="amt_should_not be_greater_than_called_amt")
          ]

    @property
    def rem_amt(self):
        return self.called_amt - self.funded_amt

    def cal_status(self):
        if self.rem_amt <= 0:
            return self.Status.FUNDED
        if self.rem_amt > 0:
            return self.Status.PARTIALLY_FUNDED
        return self.Status.OPEN

class Transaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = "credit"
        DEBIT = "debit"

    class Status(models.TextChoices):
        SUGGESTED = "suggested"
        NEEDS_REVIEW = "needs_review"
        RECONCILED = "reconciled"
        IGNORED = "ignored"

    org = models.ForeignKey( Organization, unique=True,on_delete=models.CASCADE)
    date = models.DateField()
    descp = models.TextField()
    amt = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=10, choices=Type.choices)
    bank_ref = models.CharField(unique= True, max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(type="credit", amt__gt=0) | Q(type="debit", amt__lt=0)),
                name='amt_should_be_positive'
            ),
        ]
