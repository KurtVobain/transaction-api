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
        url = f"{self.url}?balance_min=60"  # Use 'balance_min' directly
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return wallets with balance >= 60
        self.assertEqual(len(data), 2)  # wallet1 and wallet4
        for wallet in data:
            self.assertGreaterEqual(Decimal(wallet['balance']), 60)

    def test_wallet_filtering_by_balance_max(self):
        """Test filtering wallets by maximum balance."""
        url = f"{self.url}?balance_max=60"  # Use 'balance_max' directly
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return wallets with balance <= 60
        self.assertEqual(len(data), 2)  # wallet2 and wallet3
        for wallet in data:
            self.assertLessEqual(Decimal(wallet['balance']), 60)

    def test_wallet_filtering_by_balance_range(self):
        """Test filtering wallets by balance range."""
        url = f"{self.url}?balance_min=40&balance_max=90"  # Use direct parameter names
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return wallets with 40 <= balance <= 90
        self.assertEqual(len(data), 2)  # wallet2 and wallet4
        for wallet in data:
            balance = Decimal(wallet['balance'])
            self.assertGreaterEqual(balance, 40)
            self.assertLessEqual(balance, 90)

    def test_wallet_search_by_label(self):
        """Test search functionality for wallets."""
        url = f"{self.url}?filter[search]=Test%20Wallet%201"  # Use 'filter[search]' as configured in settings
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should return only "Test Wallet 1"
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['label'], 'Test Wallet 1')

    def test_wallet_ordering_by_id_asc(self):
        """Test ordering wallets by ID ascending."""
        url = f"{self.url}?sort=id"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        ids = [int(wallet['id']) for wallet in data]
        self.assertEqual(ids, sorted(ids))

    def test_wallet_ordering_by_id_desc(self):
        """Test ordering wallets by ID descending."""
        url = f"{self.url}?sort=-id"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        ids = [int(wallet['id']) for wallet in data]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_wallet_ordering_by_balance_asc(self):
        """Test ordering wallets by balance ascending."""
        url = f"{self.url}?sort=balance"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        balances = [Decimal(wallet['balance']) for wallet in data]
        self.assertEqual(balances, sorted(balances))

    def test_wallet_ordering_by_balance_desc(self):
        """Test ordering wallets by balance descending."""
        url = f"{self.url}?sort=-balance"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        balances = [Decimal(wallet['balance']) for wallet in data]
        self.assertEqual(balances, sorted(balances, reverse=True))

    def test_combined_filtering_and_ordering(self):
        """Test combining filtering and ordering."""
        url = f"{self.url}?balance_min=40&sort=-balance"  # Use 'balance_min' directly
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)

        # Should have 3 wallets with balance >= 40, ordered by balance desc
        self.assertEqual(len(data), 3)
        for wallet in data:
            self.assertGreaterEqual(Decimal(wallet['balance']), 40)

        balances = [Decimal(wallet['balance']) for wallet in data]
        self.assertEqual(balances, sorted(balances, reverse=True))


class WalletDetailAPITestCase(APITestCase):
    """Test cases for wallet detail API endpoint (GET /wallets/{id}/)."""

    def setUp(self):
        """Create test data for wallet detail tests."""
        self.wallet = Wallet.objects.create(
            label="Detail Test Wallet",
            balance=Decimal('75.25')
        )
        self.url = reverse('wallet-detail', kwargs={'pk': self.wallet.pk})

    def test_get_wallet_detail(self):
        """Test retrieving a specific wallet."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'Detail Test Wallet')
        self.assertEqual(response.data['balance'], '75.250000000000000000')
        self.assertIn('id', response.data)

    def test_get_nonexistent_wallet(self):
        """Test retrieving a non-existent wallet returns 404."""
        url = reverse('wallet-detail', kwargs={'pk': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WalletCreateAPITestCase(APITestCase):
    """Test cases for wallet creation API endpoint (POST /wallets/)."""

    def setUp(self):
        """Create test data for wallet creation tests."""
        self.url = reverse('wallet-list')
        self.valid_wallet_data = {
            'label': 'New Test Wallet',
            'balance': '50.25'
        }

    def _format_jsonapi_data(self, attributes, resource_type='Wallet'):
        """Helper method to format data as JSON:API."""
        return {
            'data': {
                'type': resource_type,
                'attributes': attributes
            }
        }

    def test_create_wallet_success(self):
        """Test successful wallet creation with valid data."""
        data = self._format_jsonapi_data(self.valid_wallet_data)
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'New Test Wallet')
        self.assertEqual(response.data['balance'], '50.250000000000000000')
        self.assertIn('id', response.data)

        # Verify wallet was actually created in database
        self.assertTrue(Wallet.objects.filter(label='New Test Wallet').exists())

    def test_create_wallet_with_default_balance(self):
        """Test wallet creation without specifying balance defaults to 0."""
        data = self._format_jsonapi_data({'label': 'Default Balance Wallet'})
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'Default Balance Wallet')
        self.assertEqual(response.data['balance'], '0.000000000000000000')

    def test_create_wallet_zero_balance(self):
        """Test wallet creation with explicitly zero balance."""
        data = self._format_jsonapi_data({
            'label': 'Zero Balance Wallet',
            'balance': '0.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['balance'], '0.000000000000000000')  # Fixed expected value

    def test_create_wallet_very_large_balance(self):
        """Test wallet creation with maximum valid balance."""
        data = self._format_jsonapi_data({
            'label': 'Large Balance Wallet',
            'balance': '99.999999999999999999'  # Maximum for decimal(20,18)
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['balance'], '99.999999999999999999')

    def test_create_wallet_response_structure(self):
        """Test that wallet creation response has correct structure."""
        data = self._format_jsonapi_data(self.valid_wallet_data)
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify required fields are present
        required_fields = ['id', 'label', 'balance']
        for field in required_fields:
            self.assertIn(field, response.data)

        # Note: In some JSON:API configurations, ID might be returned as integer
        # We'll accept either format
        self.assertTrue(isinstance(response.data['id'], (str, int)))

    def test_create_wallet_database_persistence(self):
        """Test that created wallet persists in database with correct values."""
        data = self._format_jsonapi_data({
            'label': 'Persistence Test',
            'balance': '33.44'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Fetch from database and verify
        wallet = Wallet.objects.get(label='Persistence Test')
        self.assertEqual(wallet.balance, Decimal('33.44'))
        self.assertEqual(wallet.id, int(response.data['id']))  # Handle both string and int IDs

    def test_create_multiple_wallets(self):
        """Test creating multiple wallets with same label is allowed."""
        data = self._format_jsonapi_data({
            'label': 'Duplicate Label Test',
            'balance': '10.00'
        })

        response1 = self.client.post(self.url, data, content_type='application/vnd.api+json')
        response2 = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify both wallets exist
        self.assertEqual(Wallet.objects.filter(label='Duplicate Label Test').count(), 2)


class WalletCreateValidationTestCase(APITestCase):
    """Test cases for wallet creation validation errors."""

    def setUp(self):
        """Create test data for validation tests."""
        self.url = reverse('wallet-list')

    def _format_jsonapi_data(self, attributes, resource_type='Wallet'):
        """Helper method to format data as JSON:API."""
        return {
            'data': {
                'type': resource_type,
                'attributes': attributes
            }
        }

    def test_create_wallet_missing_label(self):
        """Test wallet creation fails when label is missing."""
        data = self._format_jsonapi_data({
            'balance': '50.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # JSON:API error format - check if error contains label info
        self.assertTrue(any('label' in str(error) for error in response.data))

    def test_create_wallet_empty_label(self):
        """Test wallet creation fails when label is empty."""
        data = self._format_jsonapi_data({
            'label': '',
            'balance': '50.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('label' in str(error) for error in response.data))

    def test_create_wallet_label_too_long(self):
        """Test wallet creation fails when label exceeds max length."""
        data = self._format_jsonapi_data({
            'label': 'a' * 256,  # Assuming max length is 255
            'balance': '50.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('label' in str(error) for error in response.data))

    def test_create_wallet_negative_balance(self):
        """Test wallet creation fails with negative balance."""
        data = self._format_jsonapi_data({
            'label': 'Negative Balance Test',
            'balance': '-10.00'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('balance' in str(error) for error in response.data))

    def test_create_wallet_balance_exceeds_digit_limit(self):
        """Test wallet creation fails when balance has more than 2 digits before decimal."""
        data = self._format_jsonapi_data({
            'label': 'Exceeds Limit Test',
            'balance': '99.1234567890123456789'  # 21 digits total
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('balance' in str(error) for error in response.data))

    def test_create_wallet_invalid_balance_format(self):
        """Test wallet creation fails with invalid balance format."""
        data = self._format_jsonapi_data({
            'label': 'Invalid Balance Test',
            'balance': 'not_a_number'
        })
        response = self.client.post(self.url, data, content_type='application/vnd.api+json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any('balance' in str(error) for error in response.data))
