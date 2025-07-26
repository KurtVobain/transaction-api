from django.db import transaction, IntegrityError
from rest_framework import generics, serializers
from .models import Transaction, Wallet
from .serializers import TransactionSerializer

class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        wallet_id = serializer.validated_data['wallet_id']
        amount = serializer.validated_data['amount']

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=wallet_id)

            if wallet.balance + amount < 0:
                raise serializers.ValidationError({
                    'amount': f'Insufficient funds: {wallet.balance} available.'
                })

            wallet.balance += amount
            wallet.save()

            try:
                serializer.save(wallet=wallet)
            except IntegrityError:
                raise serializers.ValidationError({'txid': 'Duplicate txid.'})
