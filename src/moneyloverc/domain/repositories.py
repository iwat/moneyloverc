import json
import sqlite3

from moneyloverc.domain.entities import Category, Wallet


class CategoryRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.setup()

    def setup(self) -> None:
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS category (
                id TEXT PRIMARY KEY,
                parent TEXT,
                account TEXT NOT NULL,
                icon TEXT NOT NULL,
                metadata TEXT NOT NULL,
                name TEXT NOT NULL,
                type INTEGER NOT NULL,
                others TEXT NOT NULL -- JSON encoded
            );
        ''')

    def save(self, category: Category) -> None:
        self.conn.execute('''
            INSERT OR REPLACE INTO category
            (id, parent, account, icon, metadata, name, type, others)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            category.id,
            category.parent,
            category.account,
            category.icon,
            category.metadata,
            category.name,
            category.type,
            json.dumps(category.others)
        ))
        self.conn.commit()

    def load(self, id: str) -> Category | None:
        cursor = self.conn.execute('''
            SELECT id, parent, account, icon, metadata, name, type, others
            FROM category
            WHERE id = ?
        ''', (id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return Category(
            id=row[0],
            parent=row[1],
            account=row[2],
            icon=row[3],
            metadata=row[4],
            name=row[5],
            type=row[6],
            others=json.loads(row[7])
        )

class WalletRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.setup()

    def setup(self) -> None:
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS wallet (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                currency_id INTEGER NOT NULL,
                owner TEXT NOT NULL,
                transaction_notification BOOLEAN NOT NULL,
                archived BOOLEAN NOT NULL,
                account_type INTEGER NOT NULL,
                exclude_total BOOLEAN NOT NULL,
                icon TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                update_at DATETIME NOT NULL,
                is_delete BOOLEAN NOT NULL,
                list_user TEXT NOT NULL, -- JSON encoded
                balance TEXT NOT NULL, -- JSON encoded
                others TEXT NOT NULL -- JSON encoded
            );
        ''')

    def save(self, wallet: Wallet) -> None:
        self.conn.execute('''
            INSERT OR REPLACE INTO wallet
            (
                id, name, currency_id, owner, transaction_notification, archived,
                account_type, exclude_total, icon, created_at, update_at, is_delete,
                list_user, balance, others
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallet.id,
            wallet.name,
            wallet.currency_id,
            wallet.owner,
            wallet.transaction_notification,
            wallet.archived,
            wallet.account_type,
            wallet.exclude_total,
            wallet.icon,
            wallet.created_at,
            wallet.update_at,
            wallet.is_delete,
            json.dumps(wallet.list_user),
            json.dumps(wallet.balance),
            json.dumps(wallet.others)
        ))
        self.conn.commit()

    def load(self, id: str) -> Wallet | None:
        cur = self.conn.execute('''
            SELECT
                id, name, currency_id, owner, transaction_notification, archived,
                account_type, exclude_total, icon, created_at, update_at, is_delete,
                list_user, balance, others
            FROM wallet
            WHERE id = ?
        ''', (id,))
        row = cur.fetchone()
        cur.close()

        if row is None:
            return None

        return Wallet(
            id=row[0],
            name=row[1],
            currency_id=row[2],
            owner=row[3],
            transaction_notification=row[4],
            archived=row[5],
            account_type=row[6],
            exclude_total=row[7],
            icon=row[8],
            created_at=row[9],
            update_at=row[10],
            is_delete=row[11],
            list_user=json.loads(row[12]),
            balance=json.loads(row[13]),
            others=json.loads(row[14])
        )
