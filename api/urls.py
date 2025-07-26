from django.urls import path
from .views import TransactionCreateView, WalletListView, TransactionListView

urlpatterns = [
    path('transactions/', TransactionCreateView.as_view(), name='create-transaction'),
    path('transactions/list/', TransactionListView.as_view(), name='transaction-list'),
    path('wallets/', WalletListView.as_view(), name='wallet-list'),
]