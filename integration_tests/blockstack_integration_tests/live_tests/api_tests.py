"""
    Blockstack Core
    ~~~~~

    copyright: (c) 2017 by Blockstack.org

This file is part of Blockstack Core.

    Blockstack Core is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Blockstack Core is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Search. If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, re, json, time
import unittest
import requests
import argparse
import binascii
import traceback
import jsontokens

from test import test_support
from binascii import hexlify

from ysi_client import schemas
import ysi_client.storage
import ysi_client.config as ysi_config
import ysi_client.config as ysi_constants
import ysi_client.keys

BASE_URL = 'http://localhost:5000'

API_PASSWORD = ysi_config.get_config(
    ysi_constants.CONFIG_PATH).get('api_password', None)

DEFAULT_WALLET_ADDRESS = "1QJQxDas5JhdiXhEbNS14iNjr8auFT96GP"

class FakeResponseObj:
    def __init__(self):
        self.status_code = 600
        self.data = ""

class ForwardingClient:
    def __init__(self, base_url):
        self.base_url = base_url
    def get(self, endpoint, headers = {}):
        resp = requests.get(self.base_url + endpoint, headers = headers)
        ret_obj = FakeResponseObj()
        ret_obj.status_code = resp.status_code
        ret_obj.data = resp.text
        return ret_obj
    def post(self, endpoint, data, headers = {}):
        resp = requests.post(self.base_url + endpoint,
                             data = data, headers = headers)
        ret_obj = FakeResponseObj()
        ret_obj.status_code = resp.status_code
        ret_obj.data = resp.text
        return ret_obj

class APITestCase(unittest.TestCase):
    def __init__(self, methodName):
        super(APITestCase, self).__init__(methodName)
        self.app = ForwardingClient("http://localhost:6270")
    def get_request(self, endpoint, headers={}, status_code=200,
                    no_json = False):
        t_start = time.time()
        resp = self.app.get(endpoint, headers = headers)
        t_end = time.time()
        print("\nget {} time: {}s".format(endpoint, t_end - t_start))
        if not resp.status_code == status_code:
            print("Bad status code: {} => {} ".format(endpoint, resp.status_code))
            print("REQUEST ===> {} + {} <===".format(endpoint, headers))
            print("RESPONSE ===>\n {} \n<===".format(resp.data))

        self.assertEqual(resp.status_code, status_code)
        if no_json:
            return resp.data

        try:
            data = json.loads(resp.data)
            return data
        except Exception as e:
            if status_code != 200:
                return {}
            raise e

    def post_request(self, endpoint, payload, headers={}, status_code=200):
        t_start = time.time()
        resp = self.app.post(endpoint, data = json.dumps(payload), headers = headers)
        t_end = time.time()
        print("\npost {} time: {}s".format(endpoint, t_end - t_start))
        if not resp.status_code == status_code:
            print("{} => {} ".format(endpoint, resp.status_code))

        self.assertEqual(resp.status_code, status_code)
        try:
            data = json.loads(resp.data)
            return data
        except Exception as e:
            if status_code != 200:
                return {}
            traceback.print_exc()
            raise e

def get_auth_header(key = None, port = 8888):
    if key is None:
        key = API_PASSWORD
    return {'Authorization' : 'bearer {}'.format(key),
            'Origin' : 'http://localhost:{}'.format(port)}

def check_data(cls, data, required_keys={}):
    for k in required_keys:
        cls.assertIn(k, data)
        if type(required_keys[k]) == dict:
            check_data(cls, data[k], required_keys = required_keys[k])
        if type(required_keys[k]) == str:
            cls.assertRegexpMatches(data[k], required_keys[k])
        if type(required_keys[k]) == int:
            cls.assertGreaterEqual(data[k], required_keys[k])

class PingTest(APITestCase):
    def test_found_user_lookup(self):
        data = self.get_request("/v1/ping",
                                headers = {} , status_code=200)

        self.assertTrue(data['status'] == 'alive')

class AuthInternal(APITestCase):
    def test_get_and_use_session_token_domain(self):
        privkey = ("a28ea1a6f11fb1c755b1d102990d64d6" +
                   "b4468c10705bbcbdfca8bc4497cf8da8")

        # test support for the development UI port as well (3000)
        auth_header = get_auth_header(port = 3000)
        request = {
            'app_domain': 'test.com',
            'app_public_key': ysi_client.keys.get_pubkey_hex(privkey),
            'methods': ['wallet_read', 'user_read'],
        }

        signer = jsontokens.TokenSigner()
        package = signer.sign(request, privkey)

        url = "/v1/auth?authRequest={}".format(package)
        data = self.get_request(url, headers = auth_header, status_code=200)

        self.assertIn('token', data)
        session = data['token']

        auth_header = get_auth_header(session)

        # test wrong origin
        data = self.get_request('/v1/wallet/payment_address',
                                headers = auth_header, status_code=403)
        # test correct origin
        auth_header['Origin'] = 'http://test.com'
        data = self.get_request('/v1/wallet/payment_address',
                                headers = auth_header, status_code=200)

        data = self.get_request('/v1/users/ablankstein.id',
                                headers = auth_header, status_code=200)
        # self.assertIn('error', data)

    def test_get_and_use_session_token_url(self):
        privkey = ("a28ea1a6f11fb1c755b1d102990d64d6" +
                   "b4468c10705bbcbdfca8bc4497cf8da8")

        # test support for the development UI port as well (3000)
        auth_header = get_auth_header(port = 3000)
        request = {
            'app_domain': 'http://test.com',
            'app_public_key': ysi_client.keys.get_pubkey_hex(privkey),
            'methods': ['wallet_read', 'user_read'],
        }

        signer = jsontokens.TokenSigner()
        package = signer.sign(request, privkey)

        url = "/v1/auth?authRequest={}".format(package)
        data = self.get_request(url, headers = auth_header, status_code=200)

        self.assertIn('token', data)
        session = data['token']

        auth_header = get_auth_header(session)

        # test wrong origin
        data = self.get_request('/v1/wallet/payment_address',
                                headers = auth_header, status_code=403)
        # test correct origin
        auth_header['Origin'] = 'http://test.com'
        data = self.get_request('/v1/wallet/payment_address',
                                headers = auth_header, status_code=200)

        data = self.get_request('/v1/users/ablankstein.id',
                                headers = auth_header, status_code=200)

    def test_auth_token_no_username(self):
        auth_header = get_auth_header()

        test_string = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NksifQ.eyJhcHBfZG9tYWluIjoiaGVsbG9ibG9ja3N0YWNrLmNvbSIsIm1ldGhvZHMiOltdLCJhcHBfcHVibGljX2tleSI6IjAyYjk0ZjY4NDgzOGFkMjdmZTE0Nzk1MGMyNjQ1ZjRhYzhjYmU1OTJlYjYzYmQwYTQ5MWQ2YzBlYWZjNjE0YzVjMCJ9.0lLrxt8uGtB2rCKB9sb0jK1DdrrWuuuWM-nsyjvFnmjNx0XfG14Npl72w6hp9W2OHoXdPe7VuXkfvKmVNlQdeA"

        url = "/v1/auth?authRequest={}".format(test_string)
        data = self.get_request(url, headers = auth_header, status_code=200)
        self.assertIn('token', data)

    def test_auth_new_token_no_username_issue483(self):
        auth_header = get_auth_header()
        test_string = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NksifQ.eyJ2ZXJzaW9uIjoxLCJibG9ja2NoYWluX2lkIjpudWxsLCJhcHBfcHJpdmF0ZV9rZXkiOiIxNDYwYWIyY2RjZmE1NDQwNzc5YWYwZDA0NWIzZTFlMjE5MjY4OGRjZTA5NDk4YWMyNDBkMTdjNzA2YWRiOThkIiwiYXBwX2RvbWFpbiI6Imh0dHA6Ly9sb2NhbGhvc3Q6NTAwMCIsIm1ldGhvZHMiOlsiIl0sImFwcF9wdWJsaWNfa2V5cyI6W3sicHVibGljX2tleSI6IjAzYTJhZmYyODhlYjI1NzVjZjE3ZTBjODc0NDZlNWExMDdmOTFkZjMzMjk5MjNkNDNmMDhmYTFmNzdlZDE0MTNmMCIsImRldmljZV9pZCI6IjAifV0sImRldmljZV9pZCI6IjAifQ.-uT-lOrvQDBZJWdg8p53LmEYBw1C8dVyGSAn96nR49MGSlNXP0vD7JsasjI6cbn9JSqGPFq1EpPLaHACkmyMcQ"
        url = "/v1/auth?authRequest={}".format(test_string)
        data = self.get_request(url, headers = auth_header, status_code=200)
        self.assertIn('token', data)

class UsersInternal(APITestCase):
    def test_get_users(self):
        user = "muneeb.id"
        data = self.get_request('/v1/users/{}'.format(user),
                                headers = get_auth_header(), status_code=200)
        to_check = {
            "@type": True,
        }
        check_data(self, data, to_check)

class LookupUsersTest(APITestCase):
    def test_found_user_lookup(self):
        base_url = '/v1/names/{}'
        url = base_url.format('muneeb.id')
        data = self.get_request(url, headers = {}, status_code=200)

        self.assertTrue(data['status'] == 'registered')

        to_check = {'address': schemas.OP_ADDRESS_PATTERN,
                    'zonefile_hash' : schemas.OP_ZONEFILE_HASH_PATTERN,
                    'last_txid' : schemas.OP_TXID_PATTERN}
        check_data(self, data, to_check)

        url = base_url.format('muneeb')
        data = self.get_request(url, headers = {}, status_code=500)
        self.assertTrue(data['error'] == 'Failed to lookup name')

    def test_get_all_names(self):
        data = self.get_request("/v1/names?page=0",
                                headers = {} , status_code=200)
        self.assertEqual(len(data), 100, "Paginated name length != 100")
        data = self.get_request("/v1/names",
                                headers = {} , status_code=401)
        data = self.get_request("/v1/names?page=10000",
                                headers = {} , status_code=200)

class Zonefiles(APITestCase):
    def test_get_zonefile(self):
        zf_url = '/v1/names/{}/zonefile'
        zf_hash_url = '/v1/names/{}/zonefile/{}'
        user = 'muneeb.id'

        zf_data = self.get_request(zf_url.format(user),
                                   headers = {}, status_code = 200)
        self.assertIn('zonefile', zf_data)

        zf_hash = ysi_client.storage.get_zonefile_data_hash(zf_data['zonefile'])
        zf_data_historic_lookup = self.get_request(zf_hash_url.format(user, zf_hash),
                                                   headers = {}, status_code = 200)
        self.assertEqual(zf_data_historic_lookup['zonefile'],
                         zf_data['zonefile'])

class NameHistoryTest(APITestCase):
    def build_url(self, username):
        return '/v1/names/{}/history'.format(username)

    def check_history_block(self, blocks):
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertRegexpMatches(block['address'], schemas.OP_ADDRESS_PATTERN)
        self.assertTrue(block['opcode'].startswith('NAME'))

    def test_found_user_lookup(self):
        usernames = 'muneeb.id'
        data = self.get_request(self.build_url(usernames),
                                headers = {}, status_code=200)

        self.assertTrue(len(data.keys()) > 2)
        for block_key, block_data in data.items():
            self.check_history_block(block_data)


class NamesOwnedTest(APITestCase):
    def build_url(self, addr):
        return '/v1/addresses/bitcoin/{}'.format(addr)
    def test_check_names(self):
        addrs_to_check = ["1J3PUxY5uDShUnHRrMyU6yKtoHEUPhKULs"]
        names_to_check = ["muneeb.id"]
        for addr, name in zip(addrs_to_check, names_to_check):
            data = self.get_request(self.build_url(addr),
                                    headers = {}, status_code = 200)
            self.assertTrue(len(data["names"]) > 0)
            self.assertIn(name, data["names"])

class NamespaceTest(APITestCase):
    def test_id_space(self):
        data = self.get_request("/v1/namespaces",
                                headers = {} , status_code=200)
        self.assertIn('id', data)

        data = self.get_request('/v1/namespaces/id', headers = {}, status_code = 200)
        to_check = {
            "address": schemas.OP_ADDRESS_PATTERN,
            "block_number": 0,
            "history": True,
            "namespace_id": True,
            "op": True,
            "op_fee": 0,
            "preorder_hash": schemas.OP_HEX_PATTERN,
            "ready_block": 0,
            "reveal_block": 0,
            "sender": schemas.OP_HEX_PATTERN,
            "sender_pubkey": schemas.OP_PUBKEY_PATTERN,
            "txid": schemas.OP_TXID_PATTERN
        }

        check_data(self, data, to_check)

    def test_id_space_names(self):
        data = self.get_request("/v1/namespaces/id/names?page=0",
                                headers = {} , status_code=200)
        self.assertEqual(len(data), 100, "Paginated name length != 100")
        data = self.get_request("/v1/namespaces/id/names",
                                headers = {} , status_code=401)



class Prices(APITestCase):
    def test_id_price(self):
        price_url = "/v1/prices/names/{}"
        data = self.get_request(price_url.format("muneeb.id"),
                                headers = {} , status_code=200)
        json_keys = data.keys()
        self.assertIn('name_price', json_keys)
        self.assertIn('preorder_tx_fee', json_keys)
        self.assertIn('register_tx_fee', json_keys)
        self.assertIn('total_estimated_cost', json_keys)
        self.assertIn('total_tx_fees', json_keys)

    def test_ns_price(self):
        data = self.get_request("/v1/prices/namespaces/id",
                                headers = {} , status_code=200)
        check_data(self, data, {'satoshis':0})

class BlockChains(APITestCase):
    def test_consensus(self):
        data = self.get_request("/v1/blockchains/bitcoin/consensus",
                                headers = {} , status_code=200)
        self.assertRegexpMatches(data['consensus_hash'], schemas.OP_CONSENSUS_HASH_PATTERN)
    def no_test_name_history(self):
        """ this is currently an unimplemented endpoint """
        data = self.get_request("/v1/blockchains/bitcoin/names/muneeb.id/history",
                                headers = {} , status_code=405)
    def test_names_pending(self):
        data = self.get_request("/v1/blockchains/bitcoin/pending",
                                headers = {} , status_code=200)
        self.assertIn("queues", data)
    def test_operations(self):
        data = self.get_request("/v1/blockchains/bitcoin/operations/456383",
                                headers = {} , status_code=200)

        to_check = {"address" : schemas.OP_ADDRESS_PATTERN,
                    "block_number" : 0,
                    "consensus_hash": schemas.OP_CONSENSUS_HASH_PATTERN,
                    "first_registered": 0,
                    "history" : True,
                    "op" : True,
                    "txid": schemas.OP_HEX_PATTERN,
                    "value_hash": schemas.OP_HEX_PATTERN}
        check_data(self, data[0], to_check)

class BlockChainsInternal(APITestCase):
    def test_unspents(self):
        url = "/v1/blockchains/bitcoin/{}/unspent".format(DEFAULT_WALLET_ADDRESS)
        self.get_request(url, headers = {}, status_code = 403)
        data = self.get_request(url, headers = get_auth_header(), status_code = 200)

        self.assertTrue(len(data) >= 1)
        data = data[0]

        self.assertTrue(data['confirmations'] >= 0)
        self.assertRegexpMatches(data['out_script'], schemas.OP_HEX_PATTERN)
        self.assertRegexpMatches(data['outpoint']['hash'], schemas.OP_HEX_PATTERN)
        self.assertRegexpMatches(data['transaction_hash'], schemas.OP_HEX_PATTERN)
        self.assertTrue(data['value'] >= 0)
    def test_txs(self):
        url = "/v1/blockchains/bitcoin/txs".format(DEFAULT_WALLET_ADDRESS)
        self.post_request(url, payload = {}, headers = {}, status_code = 403)
        self.post_request(url, payload = {}, headers = get_auth_header(), status_code = 401)

class WalletInternal(APITestCase):
    def test_addresses(self):
        for endpoint in ['payment_address', 'owner_address']:
            data = self.get_request("/v1/wallet/{}".format(endpoint),
                                    headers = get_auth_header(), status_code = 200)
            self.assertRegexpMatches(data['address'], schemas.OP_ADDRESS_PATTERN)
        data = self.get_request("/v1/wallet/data_pubkey",
                                headers = get_auth_header(), status_code = 200)
        self.assertRegexpMatches(data['public_key'], schemas.OP_PUBKEY_PATTERN)
    def test_balance(self):
        data = self.get_request("/v1/wallet/balance",
                                headers = get_auth_header(), status_code = 200)
        to_check = {'balance' : { 'bitcoin' : 0, 'satoshis' : 0 } }
        check_data(self, data, to_check)
    def test_keys(self):
        data = self.get_request("/v1/wallet/keys",
                                headers = get_auth_header(), status_code = 200)
        to_check = {
            "data_privkey": schemas.OP_HEX_PATTERN,
            "data_pubkey": schemas.OP_PUBKEY_PATTERN,
            "owner_address": schemas.OP_ADDRESS_PATTERN,
            "owner_privkey": True,
            "payment_address": schemas.OP_ADDRESS_PATTERN,
            "payment_privkey": True,
        }

        check_data(self, data, to_check)

class NodeInternal(APITestCase):
    def test_registrar(self):
        self.get_request("/v1/node/registrar/state", headers = get_auth_header(),
                         status_code = 200)
    def test_get_log(self):
        self.get_request("/v1/node/log", headers = get_auth_header(),
                         status_code = 200, no_json = True)
    def test_config(self):
        data = self.get_request("/v1/node/config", headers = get_auth_header(),
                                status_code = 200)
        to_check = { "bitcoind": True,
                     "blockchain-reader": True,
                     "blockchain-writer": True,
                     "ysi-client": True }

        check_data(self, data, to_check)

def test_main(args = []):
    test_classes = [PingTest, LookupUsersTest, NamespaceTest, BlockChains,
                    Prices, NamesOwnedTest, NameHistoryTest,
                    AuthInternal, BlockChainsInternal, Zonefiles, WalletInternal, NodeInternal]

    test_map = {}
    for t in test_classes:
        test_map[t.__name__] = t


    with test_support.captured_stdout() as out:
        try:
            test_support.run_unittest(PingTest)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
    out = out.getvalue()
    if out[-3:-1] != "OK":
        print(out)
        print("Failure of the ping test means the rest of the unit tests will " +
              "fail. Is the ysi api daemon running? (did you run " +
              "`ysi api start`)")
        sys.exit(1)

    if len(args) == 1 and args[0] == "--list":
        print("Tests supported: ")
        for testname in test_map.keys():
            print(testname)
        return

    test_runner = test_support.run_unittest

    if "--xunit-path" in args:
        ainx = args.index("--xunit-path")
        del args[ainx]
        from xmlrunner import XMLTestRunner
        test_runner = XMLTestRunner(output=args[ainx]).run
        del args[ainx]

    if "--api_password" in args:
        ainx = args.index("--api_password")
        del args[ainx]
        global API_PASSWORD
        API_PASSWORD = args[ainx]
        del args[ainx]

    if len(args) == 0 or args[0] == "--all":
        args = [ testname for testname in test_map.keys() ]

    test_suite = unittest.TestSuite()
    for test_name in args:
        test_suite.addTest( unittest.TestLoader().loadTestsFromTestCase(test_map[test_name]) )
    result = test_runner( test_suite )
    if result: # test_support.run_unittest returns None
        if result.wasSuccessful():
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == '__main__':
    test_main(sys.argv[1:])
