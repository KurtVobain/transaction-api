from django.db import transaction, IntegrityError
from rest_framework import generics, serializers, filters
from django_filters.rest_framework import DjangoFilterBackend

from .filters import WalletFilter
from .models import Transaction, Wallet
from .serializers import TransactionSerializer, WalletSerializer

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


class WalletListView(generics.ListAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = WalletFilter
    ordering_fields = ['id', 'label', 'balance']
    search_fields = ['label']
