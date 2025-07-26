from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Self

from moneyloverc.domain.enums import CategoryType


@dataclass
class Address:
    '''Information about the merchant's address.'''
    name: str
    icon: str | None
    details: str | None
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            name=data.get('name', ''),
            icon=data.get('icon', ''),
            details=data.get('details', ''),
            others={
                k: v
                for k, v in data.items()
                if k not in ['name', 'icon', 'details']
            }
        )

    def __str__(self):
        return f'Address[{self.name} {self.icon} {self.details}]'

@dataclass
class UserInfo:
    '''Information about the logged in user.'''
    id: str
    device_id: str
    email: str
    icon_package: list[str]
    purchased: bool
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data.get('_id', ''),
            device_id=data.get('deviceId', ''),
            email=data.get('email', ''),
            icon_package=data.get('icon_package', []),
            purchased=data.get('purchased', False),
            others={
                k: v
                for k, v in data.items()
                if k not in ['_id', 'deviceId', 'email', 'icon_package', 'purchased']
            }
        )

    def __str__(self):
        return f'UserInfo[{self.id} {self.email} @ {self.device_id}]'

@dataclass
class Wallet:
    '''Information about wallet.'''
    id: str
    name: str
    currency_id: int
    owner: str
    transaction_notification: bool
    archived: bool
    account_type: int
    exclude_total: bool
    icon: str
    list_user: list[dict[str, str]]
    created_at: datetime
    update_at: datetime
    is_delete: bool
    balance: list[dict[str, str]]
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        created_at = data.get('createdAt')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now()

        update_at = data.get('updateAt')
        if isinstance(update_at, str):
            update_at = datetime.fromisoformat(update_at.replace('Z', '+00:00'))
        elif update_at is None:
            update_at = datetime.now()

        return cls(
            id=data.get('_id', ''),
            name=data.get('name', ''),
            currency_id=data.get('currency_id', 0),
            owner=data.get('owner', ''),
            transaction_notification=data.get('transaction_notification', False),
            archived=data.get('archived', False),
            account_type=data.get('account_type', 0),
            exclude_total=data.get('exclude_total', False),
            icon=data.get('icon', ''),
            list_user=data.get('listUser', []),
            created_at=created_at,
            update_at=update_at,
            is_delete=data.get('isDelete', False),
            balance=data.get('balance', []),
            others={
                k: v
                for k, v in data.items()
                if k not in [
                    '_id', 'name', 'currency_id', 'owner', 'transaction_notification',
                    'archived', 'account_type', 'exclude_total', 'icon', 'listUser',
                    'updateAt', 'isDelete', 'balance', 'createdAt'
                ]
            }
        )

    def __str__(self):
        if self.balance:
            return f'Wallet[{self.id} {self.name} cur:{self.currency_id} bal:{self.balance}]'
        return f'Wallet[{self.id} {self.name} cur:{self.currency_id}]'

@dataclass
class Campaign:
    '''Information about an event.'''
    id: str
    name: str
    icon: str
    type: int
    start_amount: int
    goal_amount: int
    owner: str
    end_date: datetime
    last_edit_by: str
    token_device: str
    currency_id: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    is_delete: bool
    status: bool
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        def parse_date(date_str):
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.now()

        return cls(
            id=data.get('_id', ''),
            name=data.get('name', ''),
            icon=data.get('icon', ''),
            type=data.get('type', 0),
            start_amount=data.get('start_amount', 0),
            goal_amount=data.get('goal_amount', 0),
            owner=data.get('owner', ''),
            end_date=parse_date(data.get('end_date')),
            last_edit_by=data.get('lastEditBy', ''),
            token_device=data.get('tokenDevice', ''),
            currency_id=data.get('currency_id', 0),
            is_public=data.get('isPublic', False),
            created_at=parse_date(data.get('created_at')),
            updated_at=parse_date(data.get('updated_at')),
            is_delete=data.get('isDelete', False),
            status=data.get('status', False),
            others={
                k: v
                for k, v in data.items()
                if k not in [
                    '_id', 'name', 'icon', 'type', 'start_amount',
                    'goal_amount', 'owner', 'end_date', 'lastEditBy',
                    'tokenDevice', 'currency_id', 'isPublic',
                    'created_at', 'updated_at', 'isDelete', 'status'
                ]
            }
        )

    def __str__(self):
        return f'Campaign[{self.id} {self.name} {self.type}]'

@dataclass
class Category:
    '''Information about transaction category.'''
    id: str
    parent: str | None  # parent._id, ignored icon, metadata, name, type
    account: str
    icon: str
    metadata: str
    name: str
    type: CategoryType
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if 'parent' in data:
            if type(data['parent']) == str:
                parent = data['parent']
            else:
                parent = data['parent']['_id']
        else:
            parent = None
        return cls(
            id=data.get('_id', ''),
            parent=parent,
            account=data.get('account', ''),
            icon=data.get('icon', ''),
            metadata=data.get('metadata', ''),
            name=data.get('name', ''),
            type=CategoryType(data.get('type', 1)),
            others={
                k: v
                for k, v in data.items()
                if k not in [
                    '_id', 'icon', 'metadata', 'name', 'type', 'account', 'parent'
                ]
            }
        )

    def __str__(self):
        return f'Category[{self.id} {self.name} {self.type}]'


@dataclass
class Transaction:
    '''An income or an expense entry in moneylover.'''
    id: str
    note: str
    account: Wallet | None
    category: Category | None
    amount: float
    date: datetime
    images: list[str]  # list of image file name, prefix with https://bucket.moneylover.com/
    exclude_report: bool
    campaigns: list[Campaign]
    with_: list[str]
    address: Address | None
    others: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        def parse_date(date_str):
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.now()

        account = None
        if data.get('account'):
            account = Wallet.from_dict(data['account'])

        category = None
        if data.get('category'):
            category = Category.from_dict(data['category'])

        campaigns = []
        if data.get('campaign'):
            campaigns = [Campaign.from_dict(c) for c in data['campaign']]

        address = None
        if data.get('address'):
            try:
                address = Address.from_dict(json.loads(data['address']))
            except json.decoder.JSONDecodeError:
                address = Address(data['address'], None, None, {})

        return cls(
            id=data.get('_id', ''),
            note=data.get('note', ''),
            account=account,
            category=category,
            amount=data.get('amount', 0.0),
            date=parse_date(data.get('displayDate')),
            images=data.get('images', []),
            exclude_report=data.get('exclude_report', False),
            campaigns=campaigns,
            with_=data.get('with', []),
            address=address,
            others={
                k: v
                for k, v in data.items()
                if k not in [
                    '_id', 'note', 'account', 'category', 'amount',
                    'displayDate', 'images', 'exclude_report',
                    'campaign', 'with', 'address',
                ]
            }
        )

    def __str__(self):
        return f'Tx[{self.date} {self.amount} {self.category} {self.account}]'


@dataclass
class TransactionInput:
    '''An income or an expense entry to be posted to moneylover.'''
    account: str
    category: str
    amount: float
    note: str
    date: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'account': self.account,
            'category': self.category,
            'amount': self.amount,
            'note': self.note,
            'displayDate': self.date.isoformat()
        }

    def __str__(self):
        return f'Tx[{self.date} {self.amount} {self.category} {self.account}]'
