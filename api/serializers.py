from rest_framework import serializers
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'label', 'balance']


class TransactionSerializer(serializers.ModelSerializer):
    wallet_id = serializers.IntegerField(write_only=True)
    wallet = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Transaction
        fields = ['wallet_id', 'wallet', 'amount', 'txid']
        read_only_fields = ['wallet']

    def validate_wallet_id(self, value):
        if not Wallet.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Wallet {value} not found.")
        return value

    def validate_txid(self, value):
        if Transaction.objects.filter(txid=value).exists():
            raise serializers.ValidationError("Duplicate txid.")
        return value

    def validate(self, data):
        """Prevent overdraft with a clear 'Insufficient funds' message."""
        wallet = Wallet.objects.get(id=data['wallet_id'])
        amount = data['amount']
        new_balance = wallet.balance + amount
        if new_balance < 0:
            raise serializers.ValidationError({
                'amount': f'Insufficient funds: {wallet.balance} available.'
            })
        return data

    def create(self, validated_data):
        # the view injects wallet instance into save()
        wallet = validated_data.pop('wallet')
        validated_data.pop('wallet_id', None)
        return Transaction.objects.create(wallet=wallet, **validated_data)
