# -*- coding: utf-8 -*-
"""
    Registrar
    ~~~~~
    :copyright: (c) 2014-2016 by Halfmoon Labs, Inc.
    :copyright: (c) 2016 ysi.org
    :license: MIT, see LICENSE for more details.
"""

import os
import sys
import json
import unittest

from basicrpc import Proxy
from pymongo import MongoClient

import pybitcoin
from pybitcoin import BlockcypherClient
from pybitcoin.services.blockcypher import get_unspents

# Hack around absolute paths
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(current_dir + "/../")
sys.path.insert(0, parent_dir)

from registrar.states import nameRegistered

from registrar.network import get_dht_profile
from registrar.network import get_bs_client, get_dht_client

from registrar.utils import satoshis_to_btc
from registrar.blockchain import get_tx_confirmations, recipientNotReady

from registrar.crypto.utils import get_address_from_privkey
from registrar.wallet import wallet

from registrar.config import BLOCKCYPHER_TOKEN, RATE_LIMIT

test_users = ['muneeb.id', 'fredwilson.id']
test_tx_hash = '30c2ccd9141dc21fcf9a6da508e528bc88a952efb7a1053821195f5d7db46587'


class RegistrarTestCase(unittest.TestCase):

    def tearDown(self):
        pass

    def test_blockstore_connectivity(self):
        """ Check connection to blockstore node
        """

        client = get_bs_client()
        resp = client.ping()

        self.assertDictContainsSubset({'status': 'alive'}, resp)

    def test_dht_connectivity(self):
        """ Check connection to DHT
        """

        client = get_dht_client()
        resp = client.ping()[0]

        self.assertDictContainsSubset({'status': 'alive'}, resp)

    def test_username_registered(self):
        """ Check if username is registered on blockchain
        """

        for fqu in test_users:

            resp = nameRegistered(fqu)

            self.assertTrue(resp, msg="Username not registered")

    def test_profile_data(self):
        """ Check if:
            1) correct profile data is associated with username
            2) data can be fetched from DHT
        """

        for fqu in test_users:

            profile = get_dht_profile(fqu)

            profile = json.loads(profile)

            self.assertIsInstance(profile, dict, msg="Profile not found")

    def test_inputs(self):
        """ Check if registrar's wallet has enough inputs
        """

        pass

        """
        from registrar.config import BTC_PRIV_KEY
        btc_address = get_address_from_privkey(BTC_PRIV_KEY)

        #print "Testing address: %s" % btc_address

        client = BlockcypherClient(api_key=BLOCKCYPHER_TOKEN)

        unspents = get_unspents(btc_address, client)

        total_satoshis = 0
        counter = 0
        for unspent in unspents:

            counter += 1
            total_satoshis += unspent['value']

        btc_amount = satoshis_to_btc(total_satoshis)
        btc_amount = float(btc_amount)

        self.assertGreater(btc_amount, 0.01, msg="Don't have enough inputs in btc address")
        """

    def test_tx_confirmations(self):
        """ Check if registrar can get tx confirmations from bitcoind
        """

        confirmations = get_tx_confirmations(test_tx_hash)

        self.assertGreater(confirmations, 10, msg="Error getting tx confirmations")

    def test_max_names_owned(self):
        """ Check if registrar wallet addresses own more than 20 names 
            This is a limit imposed by blockstore
        """

        list_of_addresses = wallet.get_child_keypairs(count=RATE_LIMIT)

        for address in list_of_addresses:
            resp = recipientNotReady(address)
            self.assertFalse(resp, msg="Address %s owns too many names" % address)


class WebappTestCase(unittest.TestCase):

    def tearDown(self):
        pass

    def test_db_connectivity(self):
        """ Check connection to databases
        """

        from registrar.drivers.webapp_driver import webapp_db
        users = webapp_db.user
        count = users.count()

        self.assertGreater(count, 100, msg="Cannot connect to DB")

if __name__ == '__main__':

    unittest.main()
