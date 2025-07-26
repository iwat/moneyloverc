import getpass
import logging
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from moneyloverc.domain.entities import Category, Wallet
from moneyloverc.domain.repositories import CategoryRepository, WalletRepository
from moneyloverc.domain.services import MoneyLoverClient
from configparser import ConfigParser


CONFIG_FILE = 'config.ini'


def dump_category(cat_repo: CategoryRepository,
                  category: Category):
    cat_repo.save(category)
    print(f'  - {category}')

def dump_wallet(client: MoneyLoverClient,
                wallet_repo: WalletRepository,
                cat_repo: CategoryRepository,
                wallet: Wallet):
    wallet_repo.save(wallet)

    print(f'## {wallet}')

    wallet_id = wallet.id

    categories = client.get_categories(wallet_id)
    if not categories:
        print('No categories found')
        return

    print(f'Found {len(categories)} categories in wallet {wallet.name}:')
    for category in categories[:5]:
        dump_category(cat_repo, category)

    end_date = datetime.now(ZoneInfo('UTC'))
    start_date = wallet.created_at
    current_date = start_date
    while current_date <= end_date:
        transactions = client.get_transactions(wallet_id, current_date, current_date + timedelta(days=30))
        for transaction in transactions:
            print(f'  - {transaction}')
        current_date += timedelta(days=30)

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
    print(f'# User info: {user_info}')

    wallets = client.get_wallets()
    if not wallets:
        print('No wallets found')
        return

    conn = sqlite3.connect('moneylover.db')
    wallet_repo = WalletRepository(conn)
    cat_repo = CategoryRepository(conn)

    print(f'Found {len(wallets)} wallets:')
    for wallet in wallets:
        dump_wallet(client, wallet_repo, cat_repo, wallet)
