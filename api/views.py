from django.db import transaction, IntegrityError
from rest_framework_json_api import serializers, filters
from rest_framework_json_api.views import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_json_api.django_filters import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter

from .filters import WalletFilter, TransactionFilter
from .models import Transaction, Wallet
from .serializers import TransactionSerializer, WalletSerializer


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all().select_related('wallet')
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['id', 'txid', 'amount', 'wallet__id']
    search_fields = ['txid']

    # Configure prefetching for included resources
    select_for_includes = {
        'wallet': ['wallet'],
    }

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


class WalletViewSet(ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, SearchFilter]
    filterset_class = WalletFilter
    ordering_fields = ['id', 'label', 'balance']
    search_fields = ['label']

    # Configure prefetching for included resources
    prefetch_for_includes = {
        'transactions': ['transactions'],
    }


class TransactionListView(generics.ListAPIView):
    queryset = Transaction.objects.select_related('wallet').all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['id', 'txid', 'amount', 'wallet__id']
    search_fields = ['txid']


class WalletDetailView(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
