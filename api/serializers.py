from rest_framework import serializers
from .models import Transaction, Wallet

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'label', 'balance']

class TransactionSerializer(serializers.ModelSerializer):
    wallet_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Transaction
        fields = ['wallet_id', 'amount', 'txid']

    def validate_wallet_id(self, value):
        if not Wallet.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Wallet {value} not found.")
        return value

    def validate_txid(self, value):
        if Transaction.objects.filter(txid=value).exists():
            raise serializers.ValidationError("Duplicate txid.")
        return value

    def create(self, validated_data):
        # 'wallet' injected by the view
        wallet = validated_data.pop('wallet')
        return Transaction.objects.create(wallet=wallet, **validated_data)
