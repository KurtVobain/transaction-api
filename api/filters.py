import django_filters
from .models import Wallet, Transaction

class WalletFilter(django_filters.FilterSet):
    balance_min = django_filters.NumberFilter(field_name='balance', lookup_expr='gte')
    balance_max = django_filters.NumberFilter(field_name='balance', lookup_expr='lte')
    label_contains = django_filters.CharFilter(field_name='label', lookup_expr='icontains')

    class Meta:
        model = Wallet
        fields = ['label', 'label_contains', 'balance_min', 'balance_max']

class TransactionFilter(django_filters.FilterSet):
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    txid_contains = django_filters.CharFilter(field_name='txid', lookup_expr='icontains')
    wallet = django_filters.NumberFilter(field_name='wallet__id')

    class Meta:
        model = Transaction
        fields = ['txid', 'txid_contains', 'amount_min', 'amount_max', 'wallet']
