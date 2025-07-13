# moneyloverc
moneylover.me Python client library

A Python client library for interacting with the MoneyLover API.

## Installation

```bash
pip install requests
```

## Usage

### Login with Email and Password

```python
from moneyloverc import MoneyLoverClient

# Login with credentials
client = MoneyLoverClient.login("your_email@example.com", "your_password")

# Export tokens for future use
refresh_token, client_id = client.export()
```

### Restore from Saved Tokens

```python
# Restore from saved tokens
client = MoneyLoverClient.restore(refresh_token, client_id)
client.refresh()  # Get new access token
```

### Get User Information

```python
user_info = client.get_user_info()
print(f"User: {user_info.email}")
```

### Get Wallets

```python
wallets = client.get_wallets()
for wallet in wallets:
    print(f"Wallet: {wallet.name} (ID: {wallet.id})")
```

### Get Categories

```python
wallet_id = wallets[0].id
categories = client.get_categories(wallet_id)
for category in categories:
    print(f"Category: {category.name} ({category.type})")
```

### Get Transactions

```python
from datetime import datetime, timedelta

# Get transactions for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

transactions = client.get_transactions(wallet_id, start_date, end_date)
for transaction in transactions:
    print(f"Transaction: {transaction.amount} - {transaction.note}")
```

### Add a Transaction

```python
from moneyloverc import TransactionInput

# Create a new transaction
new_transaction = TransactionInput(
    note="Coffee",
    account=wallet_id,
    category=category_id,
    amount=4.50,
    date=datetime.now()
)

# Add the transaction
result = client.add_transaction(new_transaction)
```

## Data Classes

The library provides several data classes for structured data:

- `UserInfo`: User account information
- `Wallet`: Wallet/account information
- `Category`: Transaction category information
- `Transaction`: Transaction details
- `TransactionInput`: Input for creating transactions
- `Campaign`: Event/campaign information
- `CategoryType`: Enum for income/expense categories

## Debug Mode

Enable debug mode to see HTTP requests and responses:

```python
from moneyloverc import DEBUG_PAYLOAD
DEBUG_PAYLOAD = True
```

## Example

See `example.py` for a complete example of using the client library.

## Requirements

- Python 3.7+
- requests library

## License

This project is based on the Go client library and converted to Python.
