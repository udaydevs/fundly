
from rest_framework import serializers

from .models import Transaction, CapitalCall, LineItem, Match


class CapitalCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapitalCall
        fields = '__all__'

class LineItemSerializer(serializers.ModelSerializer):
    capital_call = CapitalCallSerializer(read_only=True)
    amount_remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = LineItem
        fields = '__all__'

class MatchSerializer(serializers.ModelSerializer):
    line_item = LineItemSerializer(read_only=True)

    class Meta:
        model = Match
        fields = "__all__"

class TransactionSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
