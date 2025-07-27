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

        # Verify response structure - JSON:API format
        transaction_data = data[0]
        self.assertIn('id', transaction_data)
        self.assertIn('txid', transaction_data)
        self.assertIn('amount', transaction_data)
        self.assertIn('wallet', transaction_data)

    def test_transaction_filtering_by_wallet(self):
        """Test filtering transactions by wallet ID."""
        url = f"{self.url}?wallet={self.wallet1.id}"  # Use 'wallet' instead of 'filter[wallet_id]'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)

        # Verify all transactions belong to wallet1
        for transaction in data:
            self.assertEqual(transaction['wallet']['id'], str(self.wallet1.id))

    def test_transaction_filtering_by_amount_min(self):
        """Test filtering transactions by minimum amount."""
        url = f"{self.url}?amount_min=10"  # Use 'amount_min' directly
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return 2 transactions with amount >= 10
        self.assertEqual(len(data), 2)
        for transaction in data:
            self.assertGreaterEqual(Decimal(transaction['amount']), 10)

    def test_transaction_filtering_by_amount_max(self):
        """Test filtering transactions by maximum amount."""
        url = f"{self.url}?amount_max=20"  # Use 'amount_max' directly
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return transactions with amount <= 20
        self.assertEqual(len(data), 3)
        for transaction in data:
            self.assertLessEqual(Decimal(transaction['amount']), 20)

    def test_transaction_filtering_by_amount_range(self):
        """Test filtering transactions by amount range."""
        url = f"{self.url}?amount_min=0&amount_max=20"  # Use direct parameter names
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return transactions with 0 <= amount <= 20
        self.assertEqual(len(data), 1)  # Only PAYMENT001 with amount 15.00
        self.assertEqual(data[0]['txid'], 'PAYMENT001')

    def test_transaction_search_by_txid(self):
        """Test search functionality for transactions."""
        url = f"{self.url}?filter[search]=TX001"  # Use 'filter[search]' as configured in settings
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return only TX001
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['txid'], 'TX001')

    def test_transaction_ordering_by_amount_asc(self):
        """Test ordering transactions by amount ascending."""
        url = f"{self.url}?sort=amount"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        amounts = [Decimal(t['amount']) for t in data]
        self.assertEqual(amounts, sorted(amounts))

    def test_transaction_ordering_by_amount_desc(self):
        """Test ordering transactions by amount descending."""
        url = f"{self.url}?sort=-amount"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        amounts = [Decimal(t['amount']) for t in data]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_transaction_ordering_by_txid_asc(self):
        """Test ordering transactions by txid ascending."""
        url = f"{self.url}?sort=txid"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        txids = [t['txid'] for t in data]
        self.assertEqual(txids, sorted(txids))

    def test_combined_filtering_and_ordering(self):
        """Test combining filtering and ordering."""
        url = f"{self.url}?wallet={self.wallet1.id}&sort=-amount"  # Use 'wallet' instead of 'filter[wallet_id]'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should have 2 transactions from wallet1, ordered by amount desc
        self.assertEqual(len(data), 2)
        for transaction in data:
            self.assertEqual(transaction['wallet']['id'], str(self.wallet1.id))

        amounts = [Decimal(t['amount']) for t in data]
        self.assertEqual(amounts, sorted(amounts, reverse=True))


class TransactionDetailAPITestCase(APITestCase):
    """Test cases for transaction detail API endpoint (GET /transactions/{id}/)."""

    def setUp(self):
        """Create test data for transaction detail tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')  # Changed from 100.00 to avoid decimal overflow
        )
        self.transaction = Transaction.objects.create(
            wallet=self.wallet,
            txid="DETAIL_TEST",
            amount=Decimal('25.25')  # Changed from 50.25 to stay within limits
        )
        self.url = reverse('transaction-detail', kwargs={'pk': self.transaction.pk})

    def test_get_transaction_detail(self):
        """Test retrieving a specific transaction."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['txid'], 'DETAIL_TEST')
        self.assertEqual(response.data['amount'], '25.250000000000000000')
        self.assertEqual(response.data['wallet']['id'], str(self.wallet.id))

    def test_get_nonexistent_transaction(self):
        """Test retrieving a non-existent transaction returns 404."""
        url = reverse('transaction-detail', kwargs={'pk': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TransactionCreateAPITestCase(APITestCase):
    """Test cases for transaction creation API endpoint (POST /transactions/)."""

    def setUp(self):
        """Create test data for transaction creation tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')  # Changed from 100.00 to avoid decimal overflow
        )
        self.url = reverse('transaction-list')

    def _format_jsonapi_data(self, attributes, resource_type='Transaction'):
        """Helper method to format data as JSON:API."""
        return {
            'data': {
                'type': resource_type,
                'attributes': attributes
            }
        }

    def test_create_transaction_success_credit(self):
        """Test successful transaction creation with positive amount (credit)."""
        initial_balance = self.wallet.balance
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'CREDIT001',
            'amount': '25.50'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['txid'], 'CREDIT001')
        self.assertEqual(response.data['amount'], '25.500000000000000000')
        self.assertEqual(response.data['wallet']['id'], str(self.wallet.id))

        # Verify wallet balance increased
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance + Decimal('25.50'))

        # Verify transaction exists in database
        self.assertTrue(Transaction.objects.filter(txid='CREDIT001').exists())

    def test_create_transaction_success_debit(self):
        """Test successful transaction creation with negative amount (debit)."""
        initial_balance = self.wallet.balance
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'DEBIT001',
            'amount': '-30.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '-30.000000000000000000')

        # Verify wallet balance decreased
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance - Decimal('30.00'))

    def test_create_transaction_zero_amount(self):
        """Test transaction creation with zero amount."""
        initial_balance = self.wallet.balance
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'ZERO001',
            'amount': '0.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '0.000000000000000000')  # Fixed expected format

        # Verify wallet balance unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance)

    def test_create_transaction_response_structure(self):
        """Test that transaction creation response has correct structure."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'RESPONSE_TEST',
            'amount': '15.75'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify required fields are present
        required_fields = ['id', 'txid', 'amount', 'wallet']
        for field in required_fields:
            self.assertIn(field, response.data)

        # Note: In some JSON:API configurations, ID might be returned as integer
        # We'll accept either format
        self.assertTrue(isinstance(response.data['id'], (str, int)))

    def test_create_transaction_database_persistence(self):
        """Test that created transaction persists in database with correct values."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'PERSIST_TEST',
            'amount': '42.25'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Fetch from database and verify
        transaction = Transaction.objects.get(txid='PERSIST_TEST')
        self.assertEqual(transaction.wallet.id, self.wallet.id)
        self.assertEqual(transaction.amount, Decimal('42.25'))
        self.assertEqual(transaction.id, int(response.data['id']))  # Handle both string and int IDs


class TransactionCreateValidationTestCase(APITestCase):
    """Test cases for transaction creation validation errors."""

    def setUp(self):
        """Create test data for validation tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.00')
        )
        self.existing_transaction = Transaction.objects.create(
            wallet=self.wallet,
            txid="EXISTING_TX",
            amount=Decimal('10.00')
        )
        self.url = reverse('transaction-list')

    def _format_jsonapi_data(self, attributes, resource_type='Transaction'):
        """Helper method to format data as JSON:API."""
        return {
            'data': {
                'type': resource_type,
                'attributes': attributes
            }
        }

    def test_create_transaction_missing_wallet_id(self):
        """Test transaction creation fails when wallet_id is missing."""
        data = self._format_jsonapi_data({
            'txid': 'MISSING_WALLET',
            'amount': '10.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # JSON:API error format - check if error contains wallet_id info
        self.assertTrue(any('wallet_id' in str(error) for error in response.data))

    def test_create_transaction_missing_txid(self):
        """Test transaction creation fails when txid is missing."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'amount': '10.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('txid' in str(error) for error in response.data))

    def test_create_transaction_missing_amount(self):
        """Test transaction creation fails when amount is missing."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'MISSING_AMOUNT'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('amount' in str(error) for error in response.data))

    def test_create_transaction_invalid_wallet_id(self):
        """Test transaction creation fails with non-existent wallet_id."""
        data = self._format_jsonapi_data({
            'wallet_id': 99999,
            'txid': 'INVALID_WALLET',
            'amount': '10.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('wallet_id' in str(error) or 'Wallet' in str(error) for error in response.data))

    def test_create_transaction_duplicate_txid(self):
        """Test transaction creation fails with duplicate txid."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'EXISTING_TX',
            'amount': '20.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('txid' in str(error) or 'Duplicate' in str(error) for error in response.data))

    def test_create_transaction_insufficient_funds(self):
        """Test transaction creation fails when it would cause negative balance."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'OVERDRAFT',
            'amount': '-60.00'  # Wallet only has 50.00, this would overdraft
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('funds' in str(error) or 'amount' in str(error) for error in response.data))

    def test_create_transaction_invalid_amount_format(self):
        """Test transaction creation fails with invalid amount format."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'INVALID_AMOUNT',
            'amount': 'not_a_number'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('amount' in str(error) for error in response.data))

    def test_create_transaction_empty_txid(self):
        """Test transaction creation fails with empty txid."""
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': '',
            'amount': '10.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('txid' in str(error) for error in response.data))

    def test_create_transaction_amount_exceeds_digit_limit(self):
        """Test transaction creation fails with amount exceeding digit limits."""
        # Test amount with more than 20 total digits (2 before decimal, 18 after)
        data = self._format_jsonapi_data({
            'wallet_id': self.wallet.id,
            'txid': 'EXCEEDS_LIMIT',
            'amount': '99.1234567890123456789'  # 21 digits total
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('amount' in str(error) for error in response.data))
