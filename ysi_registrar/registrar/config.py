# -*- coding: utf-8 -*-
"""
    Registrar
    ~~~~~
    :copyright: (c) 2014-2016 by Halfmoon Labs, Inc.
    :copyright: (c) 2016 ysi.org
    :license: MIT, see LICENSE for more details.
"""

import os

BLOCKSTACKD_IP = 'server.ysi.org'
BLOCKSTACKD_PORT = 6264

DHT_MIRROR_IP = 'mirror.ysi.org'
DHT_MIRROR_PORT = 6266

REGISTRAR_IP = '127.0.0.1'
REGISTRAR_PORT = 6268

RESOLVER_URL = 'http://resolver.onename.com'
RESOLVER_USERS_ENDPOINT = "/v2/users/"

DEFAULT_NAMESPACE = "id"

# current defined drivers being used for registrar
REGISTRAR_DRIVERS = ['webapp', 'api']

IGNORE_USERNAMES = []
IGNORE_NAMES_STARTING_WITH = []

SERVER_MODE = True  # if registrar deployed as server vs. imported into lib

try:
    # for registrar's internal queue
    QUEUE_DB_URI = os.environ['QUEUE_DB_URI']
except:
    QUEUE_DB_URI = None

try:
    # for encrypting DB entries like privkeys
    SECRET_KEY = os.environ['SECRET_KEY']
except:
    SECRET_KEY = None

try:
    BLOCKCYPHER_TOKEN = os.environ['BLOCKCYPHER_TOKEN']
except:
    BLOCKCYPHER_TOKEN = None

try:
    HD_WALLET_PRIVKEY = os.environ['HD_WALLET_PRIVKEY']
except:
    HD_WALLET_PRIVKEY = None

DEBUG = False  # can change in config_local

if SERVER_MODE:
    UTXO_PROVIDER = "bitcoind"
else:
    UTXO_PROVIDER = 'blockcypher'

DEFAULT_HOST = '127.0.0.1'
MEMCACHED_PORT = '11211'
MEMCACHED_TIMEOUT = 15 * 60

# defined in config_local
CONSENSUS_SERVERS = []

API_WHITE_LISTED_KEYS = []

TX_FEE = 0.0002  # around 7 cents
TARGET_BALANCE_PER_ADDRESS = 0.009
MINIMUM_BALANCE = 0.002
CHAINED_PAYMENT_AMOUNT = 0.04
DEFAULT_REFILL_AMOUNT = 0.04
MAX_LENGTH_CHAINED_PAYMENT = 10

DEFAULT_WALLET_DISPLAY = 2
DEFAULT_WALLET_OFFSET = 0

MINIMUM_LENGTH_NAME = 6
MAXIMUM_LENGTH_NAME = 31  # for .id
MAXIMUM_NAMES_PER_ADDRESS = 20
MAX_DHT_WRITE = (8 * 1024) - 1

RATE_LIMIT = 100   # target tx per block
SLEEP_INTERVAL = 20  # in seconds
RETRY_INTERVAL = 10  # if a tx is not picked up by x blocks

PREORDER_CONFIRMATIONS = 6
PREORDER_REJECTED = 130  # no. of blocks after which preorder should be removed
TX_CONFIRMATIONS_NEEDED = 10
MAX_TX_CONFIRMATIONS = 130

DEFAULT_CHILD_ADDRESSES = RATE_LIMIT
QUEUE_LENGTH_TO_MONITOR = 50

CACHE_FILE = 'child_addresses.json'

# need two separate DBs because rpc daemon and monitor are not thread safe
LOCAL_STATE_DB = 'local_state.json'
PEDNING_REQUESTS_DB = 'pending_requests.json'

if SERVER_MODE:
    LOCAL_DIR = os.path.expanduser('~/.registrar')
else:
    LOCAL_DIR = os.path.expanduser('~/.ysi')

CACHE_FILE_FULLPATH = os.path.join(LOCAL_DIR, CACHE_FILE)

# default settings for bitcoind, can override in config_local
BITCOIND_SERVER = 'bitcoin.ysi.com'
BITCOIND_PORT = 8332
BITCOIND_USER = 'ysi'
BITCOIND_PASSWD = 'ysisystem'
BITCOIND_WALLET_PASSPHRASE = ''
BITCOIND_USE_HTTPS = False

UTXO_SERVER = BITCOIND_SERVER
UTXO_USER = BITCOIND_USER
UTXO_PASSWD = BITCOIND_PASSWD

DHT_IGNORE = []

try:
    from config_local import *
except Exception as e:

    email_regrex = ''  # if it's not defined in config_local
