from django.urls import path
from .views import TransactionCreateView, WalletListView

urlpatterns = [
    path('transactions/', TransactionCreateView.as_view(), name='create-transaction'),
    path('wallets/', WalletListView.as_view(), name='wallet-list'),
]