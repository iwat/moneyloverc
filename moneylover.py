#!/usr/bin/env python3
import argparse
import datetime
import getpass
import http.client
import json
import logging
import pprint
import os.path
import urllib.parse

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'
CONFIG_PATH = os.path.expanduser('~/.config/moneylover.json')


def post_for_json(url, encoded_body, headers):
	parsed_url = urllib.parse.urlparse(url)
	if parsed_url.scheme != 'https':
		raise RuntimeError(f'only https is supported, got {url}')

	actual_headers = headers.copy()
	actual_headers['User-Agent'] = USER_AGENT

	conn = http.client.HTTPSConnection(parsed_url.netloc)
	conn.request('POST', parsed_url.path, encoded_body, actual_headers)
	resp = conn.getresponse()

	if resp.status != 200:
		raise RuntimeError(f'POST error {resp.status} {resp.reason} {resp.read()}')

	result = json.loads(resp.read())
	conn.close()
	return result


def post_form(url, body, headers):
	if body is None:
		encoded_body = None
	else:
		encoded_body = urllib.parse.urlencode(body)
		logging.info(encoded_body)
	actual_headers = headers.copy()
	actual_headers['Content-Type'] = 'application/x-www-form-urlencoded'
	return post_for_json(url, encoded_body, actual_headers)


def post_json(url, body, headers):
	if body is None:
		encoded_body = None
	else:
		encoded_body = json.dumps(body)
	actual_headers = headers.copy()
	actual_headers['Content-Type'] = 'application/json'
	json_resp = post_for_json(url, encoded_body, actual_headers)
	if 'status' in json_resp and json_resp['status'] == False:
		raise ApiException(json_resp['code'], json_resp['message'])
	return json_resp


class ApiException(BaseException):
	def __init__(self, code, msg):
		self.code = code
		self.msg = msg

	def __str__(self):
		return f'{self.code}: {self.msg}'


class NotLoggedInException(BaseException):
	pass


class TransactionInfo:
	def __init__(self, wallet_id, amount, date, category, note):
		self.wallet_id = wallet_id
		self.amount = amount
		self.date = date
		self.category = category
		self.note = note

	def encode(self):
		return {
			'account': self.wallet_id,
			'amount': f'{self.amount}',
			'displayDate': self.date,
			'category': self.category,
			'note': self.note,
			'address': '{"name":"hello"}',
		}


class Client:
	def __init__(self):
		self.access_token = None
		self.refresh_token = None
		self.client_id = None

	def login(self, email, password):
		login_info = post_form('https://web.moneylover.me/api/user/login-url', None, {})
		login_url = urllib.parse.urlparse(login_info['data']['login_url'])
		login_url_query = dict(urllib.parse.parse_qsl(login_url.query))

		login_body = {'email': email, 'password': password}
		login_headers = {
			'Authorization': f'Bearer {login_info["data"]["request_token"]}',
			'Client': login_url_query['client'],
		}

		oauth_token = post_json('https://oauth.moneylover.me/token', login_body, login_headers)
		self.enact_oauth_token(oauth_token['access_token'], oauth_token['refresh_token'], login_url_query['client'])

	def enact_oauth_token(self, access_token, refresh_token, client_id):
		self.access_token = access_token
		self.refresh_token = refresh_token
		self.client_id = client_id
		self.validate_user()
		self.store_creds()

	def  store_creds(self):
		config = {
			'access_token': self.access_token,
			'refresh_token': self.refresh_token,
			'client_id': self.client_id,
		}
		with open(CONFIG_PATH, 'w') as f:
			f.write(json.dumps(config))

	def restore(self):
		if not os.path.exists(CONFIG_PATH):
			raise NotLoggedInException(f'{CONFIG_PATH} does not exist')

		with open(CONFIG_PATH, 'r') as f:
			config = json.load(f)

		try:
			self.enact_oauth_token(config['access_token'], config['refresh_token'], config['client_id'])
		except NotLoggedInException:
			new_oauth_token = self.call_refresh_token()
			self.enact_oauth_token(new_oauth_token['access_token'], new_oauth_token['refresh_token'], config['client_id'])

	def call_refresh_token(self):
		refresh_headers = {
			'Authorization': f'Bearer {self.refresh_token}',
			'Client': self.client_id,
		}
		return post_json('https://oauth.moneylover.me/refresh-token', None, refresh_headers)

	def validate_user(self):
		user_info = self.get_user_info()
		logging.info('Logged in as %s', user_info['email'])

	def get_user_info(self):
		return self.post_request('user/info')

	def list_wallets(self):
		return self.post_request('wallet/list')

	def list_categories(self, wallet_id):
		return self.post_request('category/list', {'walletId': wallet_id})

	def list_transactions(self, wallet_id):
		query = {'walletId': wallet_id, 'startDate': '2024-09-01', 'endDate': '2024-09-30'}
		return self.post_request('transaction/list', query)

	def add_transaction(self, tx: TransactionInfo):
		return self.post_request('transaction/add', tx.encode())

	def post_request(self, path, body = None, headers = None):
		if headers is None:
			actual_headers = {}
		else:
			actual_headers = headers.copy()
		actual_headers['Authorization'] = f'AuthJWT {self.access_token}'

		envelop = post_json(f'https://web.moneylover.me/api/{path}', body, actual_headers)
		if 'error' in envelop and envelop['error'] != 0:
			raise Client.make_exception(envelop['error'], envelop['msg'])
		if 'e' in envelop and envelop['e'] != '':
			raise Client.make_exception(envelop['e'], envelop['message'])
		return envelop['data']

	@staticmethod
	def make_exception(code, msg):
		if code == 717 or msg == 'token_device_not_found':
			return NotLoggedInException()
		return ApiException(code, msg)


logging.basicConfig(level=logging.INFO)

c = Client()
try:
	c.restore()
except NotLoggedInException:
	email = input('Email: ')
	password = getpass.getpass()
	c.login(email, password)


def list_wallets(_args):
	pprint.pprint(c.list_wallets())


def list_txs(args):
	pprint.pprint(c.list_transactions(args.wallet))


def add_tx(_args):
	pprint.pprint(c.add_transaction(TransactionInfo(
		wallet_id='F4A25731D9F741938C74E7279921790F',
		amount=9.99,
		date=datetime.date.today().strftime('%Y-%m-%d'),
		category='DADCDF0EC90840288B2B94DA60CD8043',
		note='test from moneyloverc',
	)))


def list_categories(args):
	pprint.pprint(c.list_categories(args.wallet))

parser = argparse.ArgumentParser(prog='moneyloverc')
subparsers = parser.add_subparsers()

wallet_parser = subparsers.add_parser('wallet')
wallet_subparsers = wallet_parser.add_subparsers()
wallet_ls_parser = wallet_subparsers.add_parser('ls')
wallet_ls_parser.set_defaults(func=list_wallets)

tx_parser = subparsers.add_parser('tx')
tx_subparsers = tx_parser.add_subparsers()
tx_ls_parser = tx_subparsers.add_parser('ls')
tx_ls_parser.add_argument('--wallet', required=True)
tx_ls_parser.set_defaults(func=list_txs)
tx_add_parser = tx_subparsers.add_parser('add')
tx_add_parser.set_defaults(func=add_tx)

cat_parser = subparsers.add_parser('cat')
cat_subparsers = cat_parser.add_subparsers()
cat_ls_parser = cat_subparsers.add_parser('ls')
cat_ls_parser.add_argument('--wallet', required=True)
cat_ls_parser.set_defaults(func=list_categories)

args = parser.parse_args()
args.func(args)