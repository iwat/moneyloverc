import getpass
import logging
from datetime import datetime, timedelta
from pprint import pprint

from moneyloverc.domain.services import MoneyLoverClient
from configparser import ConfigParser


CONFIG_FILE = 'config.ini'

def main():
    logging.basicConfig(level=logging.INFO)

    cfg = ConfigParser()
    cfg.read(CONFIG_FILE)

    client = MoneyLoverClient()

    if 'auth' not in cfg:
        cfg['auth'] = {}

    session_modified = True
    if 'refresh_token' in cfg['auth']:
        client.restore(cfg['auth']['jwt_token'], cfg['auth']['refresh_token'], cfg['auth']['client_id'])
        if int(cfg['auth']['expire']) < datetime.now().timestamp():
            client.refresh()
        else:
            logging.info('Session is still valid, no login required.')
            session_modified = False
    else:
        print('Please enter your email and password')
        email = input('Email: ')
        password = getpass.getpass(prompt='Password: ')
        client.login(email, password)

    if session_modified:
        cfg['auth']['jwt_token'] = client.jwt_token
        cfg['auth']['refresh_token'] = client.refresh_token
        cfg['auth']['client_id'] = client.client_id
        cfg['auth']['expire'] = client.expire

        with open(CONFIG_FILE, 'w') as f:
            cfg.write(f)

    user_info = client.get_user_info()
    print(f'User info: {user_info}')

    wallets = client.get_wallets()
    print(f'Found {len(wallets)} wallets:')
    for wallet in wallets:
        print(f'  - {wallet}')

    if not wallets:
        print('No wallets found')
        return

    wallet = wallets[0]
    wallet_id = wallet.id

    categories = client.get_categories(wallet_id)
    print(f'Found {len(categories)} categories in wallet {wallet.name}:')
    for category in categories[:5]:
        print(f'  - {category}')

    if len(categories) > 5:
        print(f'  ... and {len(categories) - 5} more')

    if not categories:
        print('No categories found')
        return

    category = categories[0]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    transactions = client.get_transactions(wallet_id, start_date, end_date)
    print(f'Found {len(transactions)} transactions in the last 30 days:')
    for transaction in transactions[:5]:
        print(f'  - {transaction}')
        pprint(vars(transaction))

    if len(transactions) > 5:
        print(f'  ... and {len(transactions) - 5} more')

    #try:
    #    # Create a sample transaction
    #    new_transaction = TransactionInput(
    #        note='Test transaction from Python client',
    #        account=wallet_id,
    #        category=category.id,
    #        amount=10.50,
    #        date=datetime.now()
    #    )
    #
    #    print(f'Adding transaction: {new_transaction}')
    #
    #    # Uncomment the following line to actually add the transaction
    #    # result = client.add_transaction(new_transaction)
    #    # print(f'Transaction added: {result}')
    #
    #    print('(Transaction creation is commented out to avoid test data)')
    #
    #except Exception as e:
    #    print(f'Add transaction failed: {e}')
    #
    #print('\n=== Example completed ===')
