import django_filters
from .models import Wallet

class WalletFilter(django_filters.FilterSet):
    balance_min = django_filters.NumberFilter(field_name='balance', lookup_expr='gte')
    balance_max = django_filters.NumberFilter(field_name='balance', lookup_expr='lte')
    label_contains = django_filters.CharFilter(field_name='label', lookup_expr='icontains')

    class Meta:
        model = Wallet
        fields = ['label', 'label_contains', 'balance_min', 'balance_max']