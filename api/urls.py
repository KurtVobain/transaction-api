from .views import (TransactionViewSet, WalletViewSet)

from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, TransactionViewSet

router = DefaultRouter()
router.register('wallets', WalletViewSet)
router.register('transactions', TransactionViewSet)

urlpatterns = router.urls