# Transaction API

This project is a small Django REST framework application that exposes two JSON:API endpoints:

* **Wallets** – manage wallets with a balance and label.
* **Transactions** – record credits and debits for a wallet.

The API is built with `djangorestframework-jsonapi` and supports pagination, filtering and sorting out of the box. It also includes a simple CLI command for generating test wallets.

## Endpoints

### `/wallets/`
* `GET /wallets/` – list wallets with optional pagination, ordering and filtering.
* `POST /wallets/` – create a new wallet.
* `GET /wallets/{id}/` – retrieve details for a single wallet.

#### Wallet query parameters
| Name | Description |
|------|-------------|
| `balance_min` | Minimum balance filter. |
| `balance_max` | Maximum balance filter. |
| `label` | Exact label match. |
| `label_contains` | Case‑insensitive search in labels. |
| `filter[search]` | Search by label using DRF search filter. |
| `sort` | Field to order by (e.g. `sort=balance` or `sort=-balance`). |
| `page[number]`, `page[size]` | Pagination parameters. |

#### Wallet POST body
```json
{
  "data": {
    "type": "Wallet",
    "attributes": {
      "label": "My Wallet",
      "balance": "10.00"
    }
  }
}
```

Example response:
```json
{
  "id": "1",
  "label": "My Wallet",
  "balance": "10.000000000000000000"
}
```

#### cURL examples
```bash
# List wallets
curl -H "Accept: application/vnd.api+json" \
  http://localhost:8000/wallets/

# Retrieve a single wallet
curl -H "Accept: application/vnd.api+json" \
  http://localhost:8000/wallets/1/

# Create a wallet
curl -X POST -H "Content-Type: application/vnd.api+json" \
  -d '{"data": {"type": "Wallet", "attributes": {"label": "My Wallet", "balance": "10.00"}}}' \
  http://localhost:8000/wallets/
```

### `/transactions/`
* `GET /transactions/` – list transactions with optional pagination, ordering and filtering.
* `POST /transactions/` – create a transaction and update the wallet balance atomically.
* `GET /transactions/{id}/` – retrieve a single transaction.

#### Transaction query parameters
| Name | Description |
|------|-------------|
| `wallet` | Filter by wallet ID. |
| `amount_min` | Minimum transaction amount. |
| `amount_max` | Maximum transaction amount. |
| `txid` | Exact match for transaction ID. |
| `txid_contains` | Case‑insensitive search by transaction ID. |
| `filter[search]` | Search by `txid`. |
| `sort` | Field to order by (e.g. `sort=amount` or `sort=-amount`). |
| `page[number]`, `page[size]` | Pagination parameters. |

#### Transaction POST body
```json
{
  "data": {
    "type": "Transaction",
    "attributes": {
      "wallet_id": 1,
      "txid": "ABC123",
      "amount": "-5.00"
    }
  }
}
```

Example response:
```json
{
  "id": "1",
  "wallet": { "id": "1", "label": "My Wallet", "balance": "5.000000000000000000" },
  "txid": "ABC123",
  "amount": "-5.000000000000000000"
}
```

#### cURL examples
```bash
# List transactions
curl -H "Accept: application/vnd.api+json" \
  http://localhost:8000/transactions/

# Retrieve a single transaction
curl -H "Accept: application/vnd.api+json" \
  http://localhost:8000/transactions/1/

# Create a transaction
curl -X POST -H "Content-Type: application/vnd.api+json" \
  -d '{"data": {"type": "Transaction", "attributes": {"wallet_id": 1, "txid": "ABC123", "amount": "-5.00"}}}' \
  http://localhost:8000/transactions/
```

### Pagination, sorting and filtering
The API uses JSON:API compatible query parameters. Pagination is available via `page[number]` and `page[size]`. Sorting is done with `sort` where a minus sign indicates descending order. Filtering uses the query parameters listed above. Parameters can be combined, for example:

```
GET /transactions/?wallet=1&amount_min=0&sort=-amount&page[number]=2&page[size]=10
```

## Development setup

### Environment variables
Create a `.env` file in the project root containing at least:
```
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://app_user:strong_password@db:5432/app_db
```

### Docker
Build the containers and start the stack:
```bash
docker-compose build
docker-compose up
```
The application will be available on `http://localhost:8000/` and the database on port `5432`.

To run the unit tests:
```bash
docker-compose run --rm web python manage.py test
```

To seed the database with random wallets for testing, use the custom CLI command:
```bash
docker-compose run --rm web python manage.py seed_wallets 50
```
The numeric argument is optional and defaults to `50`.

## Linting and CI
The project uses **flake8** for linting. A GitHub Actions workflow runs flake8 and the Django test suite on every push.