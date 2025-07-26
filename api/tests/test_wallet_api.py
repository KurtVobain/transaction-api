"""
Tests for Wallet API endpoints.

This module contains tests for the wallet ViewSet which provides:
- GET /wallets/ (list wallets with filtering, search, ordering)
- GET /wallets/{id}/ (retrieve specific wallet)
- POST /wallets/ (create new wallet)
- PUT/PATCH /wallets/{id}/ (update wallet) - future implementation
- DELETE /wallets/{id}/ (delete wallet) - future implementation
"""

from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from ..models import Wallet


class WalletListAPITestCase(APITestCase):
    """Test cases for wallet list API endpoint (GET /wallets/)."""
    
    def setUp(self):
        """Create test data for wallet tests."""
        self.wallet1 = Wallet.objects.create(
            label="Test Wallet 1",
            balance=Decimal('99.50')
        )
        self.wallet2 = Wallet.objects.create(
            label="Test Wallet 2",
            balance=Decimal('50.75')
        )
        self.wallet3 = Wallet.objects.create(
            label="Another Wallet",
            balance=Decimal('0')
        )
        self.wallet4 = Wallet.objects.create(
            label="High Balance Wallet",
            balance=Decimal('80.00')
        )
        self.url = reverse('wallet-list')

    def test_get_wallet_list(self):
        """Test basic wallet list retrieval."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 4)

        # Verify response structure
        wallet_data = data[0]
        self.assertIn('id', wallet_data)
        self.assertIn('label', wallet_data)
        self.assertIn('balance', wallet_data)
        self.assertEqual(wallet_data['label'], "Test Wallet 1")
        self.assertEqual(wallet_data['balance'], "99.500000000000000000")

    def test_wallet_filtering_by_balance_min(self):
        """Test filtering wallets by minimum balance."""
        response = self.client.get(self.url, {'balance_min': '50'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 3)
        
        for wallet in data:
            self.assertGreaterEqual(Decimal(wallet['balance']), Decimal('50'))

    def test_wallet_filtering_by_balance_max(self):
        """Test filtering wallets by maximum balance."""
        response = self.client.get(self.url, {'balance_max': '80.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 3)
        
        for wallet in data:
            self.assertLessEqual(Decimal(wallet['balance']), Decimal('80.00'))

    def test_wallet_filtering_by_balance_range(self):
        """Test filtering wallets by balance range."""
        response = self.client.get(self.url, {
            'balance_min': '30',
            'balance_max': '100'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 3)  # wallet1, wallet2, wallet4

    def test_wallet_filtering_by_label_contains(self):
        """Test filtering wallets by label contains."""
        response = self.client.get(self.url, {'label_contains': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 2)
        
        for wallet in data:
            self.assertIn('Test', wallet['label'])

    def test_wallet_filtering_by_exact_label(self):
        """Test filtering wallets by exact label."""
        response = self.client.get(self.url, {'label': 'Another Wallet'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['label'], 'Another Wallet')

    def test_wallet_search_by_label(self):
        """Test search functionality for wallets."""
        response = self.client.get(self.url, {'search': 'High'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['label'], 'High Balance Wallet')

    def test_wallet_ordering_by_id_asc(self):
        """Test ordering wallets by ID ascending."""
        response = self.client.get(self.url, {'ordering': 'id'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        ids = [w['id'] for w in data]
        self.assertEqual(ids, sorted(ids))

    def test_wallet_ordering_by_id_desc(self):
        """Test ordering wallets by ID descending."""
        response = self.client.get(self.url, {'ordering': '-id'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        ids = [w['id'] for w in data]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_wallet_ordering_by_balance_asc(self):
        """Test ordering wallets by balance ascending."""
        response = self.client.get(self.url, {'ordering': 'balance'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        balances = [Decimal(w['balance']) for w in data]
        self.assertEqual(balances, sorted(balances))

    def test_wallet_ordering_by_balance_desc(self):
        """Test ordering wallets by balance descending."""
        response = self.client.get(self.url, {'ordering': '-balance'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        balances = [Decimal(w['balance']) for w in data]
        self.assertEqual(balances, sorted(balances, reverse=True))

    def test_combined_filtering_and_ordering(self):
        """Test combining filtering and ordering."""
        response = self.client.get(self.url, {
            'balance_min': '50',
            'ordering': '-balance'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        balances = [Decimal(w['balance']) for w in data]
        
        # Verify all results match filter
        for bal in balances:
            self.assertGreaterEqual(bal, Decimal('50'))
        
        # Verify ordering
        self.assertEqual(balances, sorted(balances, reverse=True))

    def test_empty_filter_results(self):
        """Test filtering that returns no results."""
        response = self.client.get(self.url, {'balance_min': '200'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 0)


class WalletDetailAPITestCase(APITestCase):
    """Test cases for wallet detail API endpoint (GET /wallets/{id}/)."""
    
    def setUp(self):
        """Create test data for wallet detail tests."""
        self.wallet = Wallet.objects.create(
            label="Test Wallet",
            balance=Decimal('50.75')
        )

    def test_get_wallet_detail(self):
        """Test retrieving a specific wallet."""
        url = reverse('wallet-detail', kwargs={'pk': self.wallet.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.wallet.id)
        self.assertEqual(response.data['label'], "Test Wallet")
        self.assertEqual(response.data['balance'], "50.750000000000000000")

    def test_get_wallet_detail_not_found(self):
        """Test retrieving a non-existent wallet returns 404."""
        url = reverse('wallet-detail', kwargs={'pk': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WalletCreateAPITestCase(APITestCase):
    """Test cases for wallet creation API endpoint (POST /wallets/)."""
    
    def setUp(self):
        """Set up test data for wallet creation tests."""
        self.url = reverse('wallet-list')
        self.valid_wallet_data = {
            'label': 'New Test Wallet',
            'balance': '50.25'
        }

    def test_create_wallet_success(self):
        """Test successful wallet creation with valid data."""
        response = self.client.post(self.url, self.valid_wallet_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'New Test Wallet')
        self.assertEqual(response.data['balance'], '50.250000000000000000')
        self.assertIn('id', response.data)
        
        # Verify wallet was actually created in database
        self.assertTrue(Wallet.objects.filter(label='New Test Wallet').exists())

    def test_create_wallet_with_default_balance(self):
        """Test wallet creation without specifying balance defaults to 0."""
        data = {'label': 'Default Balance Wallet'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'Default Balance Wallet')
        self.assertEqual(response.data['balance'], '0.000000000000000000')

    def test_create_wallet_zero_balance(self):
        """Test wallet creation with explicitly zero balance."""
        data = {
            'label': 'Zero Balance Wallet',
            'balance': '0.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['balance'], '0.000000000000000000')

    def test_create_wallet_very_large_balance(self):
        """Test wallet creation with maximum valid balance."""
        large_balance = '99.999999999999999999'  # Max value for 2 digits before decimal
        data = {
            'label': 'Large Balance Wallet',
            'balance': large_balance
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['balance'], large_balance)

    def test_create_wallet_response_structure(self):
        """Test that wallet creation response has correct structure."""
        data = {
            'label': 'Structure Test Wallet',
            'balance': '75.50'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response contains all expected fields
        expected_fields = ['id', 'label', 'balance']
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check field types
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['label'], str)
        self.assertIsInstance(response.data['balance'], str)

    def test_create_wallet_database_persistence(self):
        """Test that created wallet persists in database with correct values."""
        initial_count = Wallet.objects.count()
        
        data = {
            'label': 'Persistence Test Wallet',
            'balance': '25.75'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check database count increased
        self.assertEqual(Wallet.objects.count(), initial_count + 1)
        
        # Retrieve and verify the created wallet
        created_wallet = Wallet.objects.get(id=response.data['id'])
        self.assertEqual(created_wallet.label, 'Persistence Test Wallet')
        self.assertEqual(created_wallet.balance, Decimal('25.75'))

    def test_create_multiple_wallets(self):
        """Test creating multiple wallets with same label is allowed."""
        data = {
            'label': 'Duplicate Label Wallet',
            'balance': '10.00'
        }
        
        # Create first wallet
        response1 = self.client.post(self.url, data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Create second wallet with same label
        response2 = self.client.post(self.url, data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Should have different IDs
        self.assertNotEqual(response1.data['id'], response2.data['id'])
        
        # Both should exist in database
        duplicate_wallets = Wallet.objects.filter(label='Duplicate Label Wallet')
        self.assertEqual(duplicate_wallets.count(), 2)


class WalletCreateValidationTestCase(APITestCase):
    """Test cases for wallet creation validation errors."""
    
    def setUp(self):
        """Set up test data for validation tests."""
        self.url = reverse('wallet-list')

    def test_create_wallet_missing_label(self):
        """Test wallet creation fails when label is missing."""
        data = {'balance': '10.00'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('label', response.data)

    def test_create_wallet_empty_label(self):
        """Test wallet creation fails when label is empty."""
        data = {
            'label': '',
            'balance': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('label', response.data)

    def test_create_wallet_label_too_long(self):
        """Test wallet creation fails when label exceeds max length."""
        long_label = 'x' * 256  # Max length is 255
        data = {
            'label': long_label,
            'balance': '10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('label', response.data)

    def test_create_wallet_negative_balance(self):
        """Test wallet creation fails with negative balance."""
        data = {
            'label': 'Negative Balance Wallet',
            'balance': '-10.00'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('balance', response.data)

    def test_create_wallet_balance_exceeds_digit_limit(self):
        """Test wallet creation fails when balance has more than 2 digits before decimal."""
        data = {
            'label': 'Over Limit Wallet',
            'balance': '100.00'  # 3 digits before decimal, should fail
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('balance', response.data)
        self.assertIn('digits before the decimal', str(response.data['balance'][0]))

    def test_create_wallet_invalid_balance_format(self):
        """Test wallet creation fails with invalid balance format."""
        data = {
            'label': 'Invalid Balance Wallet',
            'balance': 'not_a_number'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('balance', response.data) 