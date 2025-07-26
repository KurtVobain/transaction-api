"""
Tests for Transaction API endpoints.

This module contains tests for the transaction ViewSet which provides:
- GET /transactions/ (list transactions with filtering, search, ordering)
- GET /transactions/{id}/ (retrieve specific transaction)
- POST /transactions/ (create new transaction with wallet balance updates)
"""

from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from ..models import Transaction, Wallet


class TransactionListAPITestCase(APITestCase):
    """Test cases for transaction list API endpoint (GET /transactions/)."""
    
    def setUp(self):
        """Create test data for transaction tests."""
        # Create wallets for testing - keep balances under 100 due to decimal field constraints
        self.wallet1 = Wallet.objects.create(
            label="Test Wallet 1", 
            balance=Decimal('50.00')
        )
        self.wallet2 = Wallet.objects.create(
            label="Test Wallet 2", 
            balance=Decimal('80.00')
        )
        
        # Create transactions for testing
        self.transaction1 = Transaction.objects.create(
            wallet=self.wallet1,
            txid="TX001",
            amount=Decimal('25.50')
        )
        self.transaction2 = Transaction.objects.create(
            wallet=self.wallet1,
            txid="TX002", 
            amount=Decimal('-10.25')
        )
        self.transaction3 = Transaction.objects.create(
            wallet=self.wallet2,
            txid="PAYMENT001",
            amount=Decimal('15.00')
        )
        self.transaction4 = Transaction.objects.create(
            wallet=self.wallet2,
            txid="REFUND001",
            amount=Decimal('-5.50')
        )
        
        self.url = reverse('transaction-list')

    def test_get_transaction_list(self):
        """Test basic transaction list retrieval."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 4)

        # Verify response structure
        transaction_data = data[0]
        expected_fields = ['wallet', 'txid', 'amount']
        for field in expected_fields:
            self.assertIn(field, transaction_data)

    def test_transaction_filtering_by_wallet(self):
        """Test filtering transactions by wallet ID."""
        response = self.client.get(self.url, {'wallet': self.wallet1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)  # TX001 and TX002
        
        for transaction in data:
            self.assertEqual(transaction['wallet'], self.wallet1.id)

    def test_transaction_filtering_by_amount_min(self):
        """Test filtering transactions by minimum amount."""
        response = self.client.get(self.url, {'amount_min': '10'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)  # TX001 and PAYMENT001
        
        for transaction in data:
            self.assertGreaterEqual(Decimal(transaction['amount']), Decimal('10'))

    def test_transaction_filtering_by_amount_max(self):
        """Test filtering transactions by maximum amount."""
        response = self.client.get(self.url, {'amount_max': '0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)  # TX002 and REFUND001 (negative amounts)
        
        for transaction in data:
            self.assertLessEqual(Decimal(transaction['amount']), Decimal('0'))

    def test_transaction_filtering_by_amount_range(self):
        """Test filtering transactions by amount range."""
        response = self.client.get(self.url, {
            'amount_min': '0',
            'amount_max': '20'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)  # Only PAYMENT001 (15.00)

    def test_transaction_filtering_by_exact_txid(self):
        """Test filtering transactions by exact txid."""
        response = self.client.get(self.url, {'txid': 'TX001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['txid'], 'TX001')

    def test_transaction_filtering_by_txid_contains(self):
        """Test filtering transactions by txid contains."""
        response = self.client.get(self.url, {'txid_contains': 'PAYMENT'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['txid'], 'PAYMENT001')

    def test_transaction_search_by_txid(self):
        """Test search functionality for transactions."""
        response = self.client.get(self.url, {'search': 'REFUND'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['txid'], 'REFUND001')

    def test_transaction_ordering_by_id_asc(self):
        """Test ordering transactions by ID ascending."""
        response = self.client.get(self.url, {'ordering': 'id'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertTrue(len(data) == 4)

    def test_transaction_ordering_by_amount_desc(self):
        """Test ordering transactions by amount descending."""
        response = self.client.get(self.url, {'ordering': '-amount'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        amounts = [Decimal(t['amount']) for t in data]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_transaction_ordering_by_txid_asc(self):
        """Test ordering transactions by txid ascending."""
        response = self.client.get(self.url, {'ordering': 'txid'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        txids = [t['txid'] for t in data]
        self.assertEqual(txids, sorted(txids))

    def test_combined_filtering_and_ordering(self):
        """Test combining filtering and ordering."""
        response = self.client.get(self.url, {
            'wallet': self.wallet1.id,
            'ordering': '-amount'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)
        
        # Verify all results are from wallet1 and ordered by amount desc
        for transaction in data:
            self.assertEqual(transaction['wallet'], self.wallet1.id)
        
        amounts = [Decimal(t['amount']) for t in data]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_empty_filter_results(self):
        """Test filtering that returns no results."""
        response = self.client.get(self.url, {'amount_min': '100'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 0)


class TransactionDetailAPITestCase(APITestCase):
    """Test cases for transaction detail API endpoint (GET /transactions/{id}/)."""
    
    def setUp(self):
        """Create test data for transaction detail tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')
        )
        self.transaction = Transaction.objects.create(
            wallet=self.wallet,
            txid="TX001",
            amount=Decimal('25.00')
        )

    def test_get_transaction_detail(self):
        """Test retrieving a specific transaction."""
        url = reverse('transaction-detail', kwargs={'pk': self.transaction.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['txid'], 'TX001')
        self.assertEqual(response.data['amount'], '25.000000000000000000')
        self.assertEqual(response.data['wallet'], self.wallet.id)

    def test_get_transaction_detail_not_found(self):
        """Test retrieving a non-existent transaction returns 404."""
        url = reverse('transaction-detail', kwargs={'pk': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TransactionCreateAPITestCase(APITestCase):
    """Test cases for transaction creation API endpoint (POST /transactions/)."""
    
    def setUp(self):
        """Set up test data for transaction creation tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')
        )
        self.url = reverse('transaction-list')

    def test_create_transaction_success_credit(self):
        """Test successful transaction creation with positive amount (credit)."""
        initial_balance = self.wallet.balance
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'CREDIT001',
            'amount': '25.50'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['txid'], 'CREDIT001')
        self.assertEqual(response.data['amount'], '25.500000000000000000')
        self.assertEqual(response.data['wallet'], self.wallet.id)
        
        # Verify wallet balance increased
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance + Decimal('25.50'))
        
        # Verify transaction exists in database
        self.assertTrue(Transaction.objects.filter(txid='CREDIT001').exists())

    def test_create_transaction_success_debit(self):
        """Test successful transaction creation with negative amount (debit)."""
        initial_balance = self.wallet.balance
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'DEBIT001',
            'amount': '-30.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '-30.000000000000000000')
        
        # Verify wallet balance decreased
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance - Decimal('30.00'))

    def test_create_transaction_zero_amount(self):
        """Test transaction creation with zero amount."""
        initial_balance = self.wallet.balance
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'ZERO001',
            'amount': '0.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '0.000000000000000000')
        
        # Verify wallet balance unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance)

    def test_create_transaction_response_structure(self):
        """Test that transaction creation response has correct structure."""
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'STRUCT001',
            'amount': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response contains expected fields but not wallet_id
        expected_fields = ['wallet', 'txid', 'amount']
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # wallet_id should not be in response (write_only)
        self.assertNotIn('wallet_id', response.data)
        
        # Check field types
        self.assertIsInstance(response.data['wallet'], int)
        self.assertIsInstance(response.data['txid'], str)
        self.assertIsInstance(response.data['amount'], str)

    def test_create_transaction_database_persistence(self):
        """Test that created transaction persists in database with correct values."""
        initial_count = Transaction.objects.count()
        
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'PERSIST001',
            'amount': '15.75'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check database count increased
        self.assertEqual(Transaction.objects.count(), initial_count + 1)
        
        # Retrieve and verify the created transaction
        created_transaction = Transaction.objects.get(txid='PERSIST001')
        self.assertEqual(created_transaction.wallet, self.wallet)
        self.assertEqual(created_transaction.amount, Decimal('15.75'))


class TransactionCreateValidationTestCase(APITestCase):
    """Test cases for transaction creation validation errors."""
    
    def setUp(self):
        """Set up test data for validation tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')
        )
        # Create existing transaction for duplicate testing
        self.existing_transaction = Transaction.objects.create(
            wallet=self.wallet,
            txid='EXISTING001',
            amount=Decimal('10.00')
        )
        self.url = reverse('transaction-list')

    def test_create_transaction_missing_wallet_id(self):
        """Test transaction creation fails when wallet_id is missing."""
        data = {
            'txid': 'MISSING001',
            'amount': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('wallet_id', response.data)

    def test_create_transaction_missing_txid(self):
        """Test transaction creation fails when txid is missing."""
        data = {
            'wallet_id': self.wallet.id,
            'amount': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('txid', response.data)

    def test_create_transaction_missing_amount(self):
        """Test transaction creation fails when amount is missing."""
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'NOAMOUNT001'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_create_transaction_invalid_wallet_id(self):
        """Test transaction creation fails with non-existent wallet_id."""
        data = {
            'wallet_id': 99999,
            'txid': 'INVALID001',
            'amount': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('wallet_id', response.data)
        self.assertIn('not found', str(response.data['wallet_id'][0]))

    def test_create_transaction_duplicate_txid(self):
        """Test transaction creation fails with duplicate txid."""
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'EXISTING001',  # Same as existing transaction
            'amount': '20.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('txid', response.data)
        # Django's default unique constraint error message
        self.assertIn('already exists', str(response.data['txid'][0]))

    def test_create_transaction_insufficient_funds(self):
        """Test transaction creation fails when it would cause negative balance."""
        # Wallet has 50.00, try to debit 60.00
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'OVERDRAFT001',
            'amount': '-60.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
        # Check for the actual error message from the view
        error_message = str(response.data['amount'][0])
        self.assertTrue('Insufficient funds' in error_message or 'available' in error_message)
        
        # Verify wallet balance unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50.00'))

    def test_create_transaction_invalid_amount_format(self):
        """Test transaction creation fails with invalid amount format."""
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'INVALID001',
            'amount': 'not_a_number'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_create_transaction_empty_txid(self):
        """Test transaction creation fails with empty txid."""
        data = {
            'wallet_id': self.wallet.id,
            'txid': '',
            'amount': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('txid', response.data)

    def test_create_transaction_amount_exceeds_digit_limit(self):
        """Test transaction creation fails with amount exceeding digit limits."""
        # Amount with more than 2 digits before decimal should fail
        data = {
            'wallet_id': self.wallet.id,
            'txid': 'OVERLIMIT001',
            'amount': '100.00'  # 3 digits before decimal, should fail
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
        # Check for decimal field constraint error
        error_message = str(response.data['amount'][0])
        self.assertIn('digits before the decimal', error_message) 