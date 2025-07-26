from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.

class Wallet(models.Model):
    label = models.CharField(max_length=255)
    balance = models.DecimalField(
        max_digits=20, 
        decimal_places=18, 
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['label']),
        ]
    
    def __str__(self):
        return f"Wallet {self.id}: {self.label} (Balance: {self.balance})"


class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    txid = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=18)
    
    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['txid']),
            models.Index(fields=['wallet']),
            models.Index(fields=['wallet', 'amount']),  # Useful for balance calculations
        ]
    
    def __str__(self):
        return f"Transaction {self.txid}: {self.amount} for Wallet {self.wallet.id}"
