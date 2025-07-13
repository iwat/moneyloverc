import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests
from moneyloverc.domain.entities import (
    Category,
    Transaction,
    TransactionInput,
    UserInfo,
    Wallet,
)


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'

CLIENT_PATTERN = re.compile(r'client=(.+?)&')

class MoneyLoverClient:
    '''Client for communicating with moneylover.'''

    def __init__(self, debug: bool = False):
        self.debug = debug

    def restore(self, jwt_token: str, refresh_token: str, client_id: str) -> None:
        logging.info('Restoring from refresh token ...')

        self.jwt_token = jwt_token
        self.refresh_token = refresh_token
        self.client_id = client_id

    def login(self, email: str, password: str) -> None:
        logging.info('Logging in ...')

        response = self._post_form('https://web.moneylover.me/api/user/login-url', {}, {})
        request_token = response['data']['request_token']
        login_url = response['data']['login_url']

        client_match = CLIENT_PATTERN.search(login_url)
        if not client_match:
            raise ValueError('Could not extract client ID from login URL')
        client_id = client_match.group(1)

        body = {
            'email': email,
            'password': password
        }
        headers = {
            'Authorization': f'Bearer {request_token}',
            'Client': client_id
        }

        token_response = self._post_json('https://oauth.moneylover.me/token', body, headers)

        if not token_response.get('status'):
            raise ValueError(f'Login failed: {token_response.get("message", "Unknown error")}')

        self.jwt_token = token_response['access_token']
        self.refresh_token = token_response['refresh_token']
        self.expire = token_response['expire']
        self.client_id = client_id

    def refresh(self) -> None:
        logging.info('Renewing access token ...')

        body = {}
        headers = {
            'Authorization': f'Bearer {self.refresh_token}',
            'Client': self.client_id
        }

        token_response = self._post_json('https://oauth.moneylover.me/refresh-token', body, headers)

        if not token_response.get('status'):
            raise ValueError(f'Refresh failed: {token_response.get("code", "")}: {token_response.get("message", "")}')

        self.jwt_token = token_response['access_token']
        self.refresh_token = token_response['refresh_token']
        self.expire = token_response['expire']

    def get_user_info(self) -> UserInfo:
        '''Retrieve UserInfo for the logged in user.'''
        response = self._post_request('/user/info', {}, {})
        return UserInfo.from_dict(response)

    def get_wallets(self) -> list[Wallet]:
        '''Retrieve a list of Wallet(s).'''
        response = self._post_request('/wallet/list', {}, {})
        return [Wallet.from_dict(wallet) for wallet in response]

    def get_categories(self, wallet_id: str) -> list[Category]:
        '''Retrieve a list of Category(s) in the given wallet.'''
        body = {'walletId': wallet_id}
        response = self._post_request('/category/list', body, {})
        return [Category.from_dict(category) for category in response]

    def get_transactions(self, wallet_id: str, start_date: datetime, end_date: datetime) -> list[Transaction]:
        '''Retrieve a list of Transaction(s).'''
        body = {
            'walletId': wallet_id,
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d')
        }
        response = self._post_request('/transaction/list', body, {})
        return [Transaction.from_dict(tx) for tx in response['transactions']]

    def add_transaction(self, transaction: TransactionInput) -> dict[str, Any]:
        '''Add the given transaction.'''
        body = {'transInfo': json.dumps(transaction.to_dict())}
        return self._post_request('/transaction/add', body, {})

    def __str__(self):
        if self.jwt_token:
            parts = self.jwt_token.split('.')
            if len(parts) >= 3:
                return f'Client[{parts[2]}]'
        return 'Client[No Token]'

    def _post_request(self, path: str, body: dict[str, Any], headers: dict[str, str]) -> Any:
        '''Make a POST request to the moneylover API.'''
        if headers is None:
            headers = {}
        headers['Authorization'] = f'AuthJWT {self.jwt_token}'

        response = self._post_form(f'https://web.moneylover.me/api{path}', body, headers)

        if response.get('error', 0) != 0:
            raise ValueError(f'Error {response["error"]}: {response.get("msg", "")}')

        if response.get('e'):
            raise ValueError(f'Error {response["e"]}: {response.get("message", "")}')

        return response.get('data')

    def _post_json(self, target_url: str, data: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        '''Make a POST request with JSON data.'''
        return self._request_json(
            target_url,
            json.dumps(data),
            headers,
            'application/json; charset=utf-8'
        )

    def _post_form(self, target_url: str, data: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        '''Make a POST request with form data.'''
        if data is None:
            data = {}

        return self._request_json(
            target_url,
            urlencode(data),
            headers,
            'application/x-www-form-urlencoded'
        )

    def _request_json(self, target_url: str, body: str, headers: dict[str, str], content_type: str) -> dict[str, Any]:
        '''Make a request and return JSON response.'''
        if headers is None:
            headers = {}

        request_headers = {
            'Content-Type': content_type,
            'User-Agent': USER_AGENT,
            **headers
        }

        if self.debug:
            print(f'Request URL: {target_url}')
            print(f'Request Headers: {request_headers}')
            print(f'Request Body: {body}')

        response = requests.post(target_url, data=body, headers=request_headers)

        if self.debug:
            print(f'Response Status: {response.status_code}')
            print(f'Response Headers: {dict(response.headers)}')
            print(f'Response Body: {response.text}')

        response.raise_for_status()
        return response.json()
