#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    Blockstack-client
    ~~~~~

    copyright: (c) 2017 by Blockstack.org

    This file is part of Blockstack-client.

    Blockstack-client is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Blockstack-client is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Blockstack-client. If not, see <http://www.gnu.org/licenses/>.
"""

import unittest, json

from ysi_client import zonefile
from ysi_client import user as user_db
from ysi_client import subdomains
import virtualchain.lib.ecdsalib as vc_ecdsa

from subdomain_registrar import util as subdomain_util

import jsonschema
from ysi_client.schemas import USER_ZONEFILE_SCHEMA
import keylib
import ysi_zones
import virtualchain

import binascii, base64, hashlib

class SubdomainZonefiles(unittest.TestCase):
    def test_basic(self):
        test_zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT "owner={}" "seqn=3" "parts=0"
        """


        fake_privkey_hex = "5512612ed6ef10ea8c5f9839c63f62107c73db7306b98588a46d0cd2c3d15ea5"
        sk = keylib.ECPrivateKey(fake_privkey_hex)
        pk = sk.public_key()
        
        test_zf = test_zf.format(subdomains.encode_pubkey_entry(pk))

        domain_name = "bar.id"

        zf_json = zonefile.decode_name_zonefile(domain_name, test_zf)

        self.assertEqual(zf_json['$origin'], domain_name)

        subds = subdomains.parse_zonefile_subdomains(domain_name, zf_json)
        self.assertEqual(len(subds), 1)
        sub = subds[0]
        self.assertEqual(sub.n, 3)
        self.assertEqual(sub.sig, None)

        self.assertEqual(sub.subdomain_name, "foo")

    def test_basic_with_multisig(self):
        test_zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT "owner={}" "seqn=3" "parts=0"
        """

        my_keys = [ keylib.ECPrivateKey() for _ in range(3) ]
        my_pubkeys = [ k.public_key().to_hex() for k in my_keys ]
        owner_addr = virtualchain.make_multisig_address(my_pubkeys, 3)

        test_zf = test_zf.format(owner_addr)

        domain_name = "bar.id"

        zf_json = zonefile.decode_name_zonefile(domain_name, test_zf)

        self.assertEqual(zf_json['$origin'], domain_name)

        subds = subdomains.parse_zonefile_subdomains(domain_name, zf_json)
        self.assertEqual(len(subds), 1)
        sub = subds[0]
        self.assertEqual(sub.n, 3)
        self.assertEqual(sub.sig, None)

        self.assertEqual(sub.subdomain_name, "foo")

    def test_sign_verify_multisig(self):
        my_keys = [ keylib.ECPrivateKey() for _ in range(9) ]
        my_pubkeys = [ k.public_key().to_hex() for k in my_keys ]
        my_sk_hexes = [ k.to_hex() for k in my_keys ]

        blob = "bar_the_foo"
        hash_hex = binascii.hexlify(hashlib.sha256(blob).digest())

        attempted_pairs = [(1, 1), (1, 2), (1, 3), (3, 3),
                           (2, 4), (3, 4), (2, 7), (5, 5)]

        for m, n in attempted_pairs:
            script_pubkeys = my_pubkeys[:n]
            redeem_script = virtualchain.make_multisig_script(script_pubkeys, m)
            owner_addr = virtualchain.make_multisig_address(script_pubkeys, m)

            sks_to_use = list(my_sk_hexes[:n])
            if m < n:
                # force 1 failed sig check during verify
                sks_to_use = sks_to_use[1:]

            sigb64 = subdomains.sign_multisig(hash_hex, redeem_script, sks_to_use)

            self.assertTrue(subdomains.verify(owner_addr, blob, sigb64))

        # try to mess with the plaintext blob
        self.assertFalse(subdomains.verify(owner_addr, blob + "0", sigb64))

        for m, n in [(2, 3)]:
            script_pubkeys = my_pubkeys[:n]
            redeem_script = virtualchain.make_multisig_script(script_pubkeys, m)
            owner_addr = virtualchain.make_multisig_address(script_pubkeys, m)

            # try with a wrong redeem script
            redeem_script_broke = virtualchain.make_multisig_script(script_pubkeys, m - 1)
            sigb64 = subdomains.sign_multisig(hash_hex, redeem_script_broke, my_sk_hexes)
            self.assertFalse(subdomains.verify(owner_addr, blob, sigb64))

    def test_parse_errs(self):
        zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT should_not_parse
        """
        domain_name = "bar.id"
        zf_json = zonefile.decode_name_zonefile(domain_name, zf)
        self.assertEqual(len(subdomains.parse_zonefile_subdomains(domain_name, zf_json)), 0)

        zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT "owner={}" "seqn=3" "should_not_parse"
        """
        zf_json = zonefile.decode_name_zonefile(domain_name, zf)
        self.assertEqual(len(subdomains.parse_zonefile_subdomains(domain_name, zf_json)), 0)

    def test_sigs(self):
        fake_privkey_hex = "5512612ed6ef10ea8c5f9839c63f62107c73db7306b98588a46d0cd2c3d15ea5"
        sk = keylib.ECPrivateKey(fake_privkey_hex)
        pk = sk.public_key()

        for t in ["foo", "bar", "bassoon"]:
            self.assertTrue(subdomains.verify(pk.address(), t,
                                              subdomains.sign(sk, t)), t)

        subdomain = subdomains.Subdomain("bar.id", "foo", subdomains.encode_pubkey_entry(sk), 3, "")

        user_zf = {
            '$origin': 'foo',
            '$ttl': 3600,
            'txt' : [], 'uri' : []
        }

        user_zf['uri'].append(zonefile.url_to_uri_record("https://foo_foo.com/profile.json"))
        jsonschema.validate(user_zf, USER_ZONEFILE_SCHEMA)

        subdomain.zonefile_str = ysi_zones.make_zone_file(user_zf)

        subdomain.add_signature(sk)

        self.assertTrue(subdomain.verify_signature(pk.address()))

        parsed_zf = zonefile.decode_name_zonefile(subdomain.subdomain_name, subdomain.zonefile_str)
        urls = user_db.user_zonefile_urls(parsed_zf)

        self.assertEqual(len(urls), 1)
        self.assertIn("https://foo_foo.com/profile.json", urls)

        self.assertRaises( NotImplementedError, lambda : subdomains.encode_pubkey_entry( fake_privkey_hex ) )

    def test_signed_transition(self):
        fake_privkey_hex = "5512612ed6ef10ea8c5f9839c63f62107c73db7306b98588a46d0cd2c3d15ea5"
        sk = keylib.ECPrivateKey(fake_privkey_hex)
        pk = sk.public_key()

        start_json = {
            "pubkey" : subdomains.encode_pubkey_entry(sk),
            "n" : 3,
            "urls":["https://foobar.com/profile",
                    "https://dropbox.com/profile2"]
        }

        next_json = {
            "pubkey" : "data:echex:0",
            "n" : 4,
            "name" : "foo",
            "urls": ["https://none.com"]
        }

        subdomain1 = subdomains.Subdomain("bar.id", "foo", subdomains.encode_pubkey_entry(sk), 3, "")
        subdomain2 = subdomains.Subdomain("bar.id", "bar", subdomains.encode_pubkey_entry(sk), 4, "")

        subdomain2.add_signature(sk)
        self.assertTrue(
            subdomains._transition_valid(subdomain1, subdomain2))

    def test_db_builder(self):
        history = [
            """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT "owner={}" "seqn=0" "parts=0"
""",
            """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
bar TXT "owner={}" "seqn=0" "parts=0"
""",
]

        foo_bar_sk = keylib.ECPrivateKey()
        bar_bar_sk = keylib.ECPrivateKey()

        history[0] = history[0].format(subdomains.encode_pubkey_entry(foo_bar_sk))
        history[1] = history[1].format(subdomains.encode_pubkey_entry(bar_bar_sk))

        domain_name = "bar.id"

        empty_zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
"""

        zf_json = zonefile.decode_name_zonefile(domain_name, empty_zf)
        self.assertEqual(zf_json['$origin'], domain_name)

        sub1 = subdomains.Subdomain(domain_name, "foo", subdomains.encode_pubkey_entry(foo_bar_sk), 1, "")
        sub2 = subdomains.Subdomain(domain_name, "bar", subdomains.encode_pubkey_entry(bar_bar_sk), 1, "")
        sub1.add_signature(foo_bar_sk)
        sub2.add_signature(bar_bar_sk)

        subdomain_util._extend_with_subdomain(zf_json, sub2)

        history.append(ysi_zones.make_zone_file(zf_json))

        zf_json = zonefile.decode_name_zonefile(domain_name, empty_zf)
        subdomain_util._extend_with_subdomain(zf_json, sub1)

        history.append(ysi_zones.make_zone_file(zf_json))

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(1)], history[:1])
        self.assertIn("foo.bar.id", subdomain_db, "Contents actually: {}".format(subdomain_db.keys()))
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertNotIn("bar.bar.id", subdomain_db)

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(2)], history[:2])
        self.assertIn("bar.bar.id", subdomain_db)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 0)

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(3)], history[:3])
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 1)

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(len(history))], history)
        self.assertEqual(subdomain_db["foo.bar.id"].n, 1)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 1)

    def test_db_builder_bad_transitions(self):
        history = [
            """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
foo TXT "owner={}" "seqn=0" "parts=0"
""",
            """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
bar TXT "owner={}" "seqn=0" "parts=0"
""",
]

        foo_bar_sk = keylib.ECPrivateKey()
        bar_bar_sk = keylib.ECPrivateKey()

        history[0] = history[0].format(subdomains.encode_pubkey_entry(foo_bar_sk))
        history[1] = history[1].format(subdomains.encode_pubkey_entry(bar_bar_sk))

        domain_name = "bar.id"

        empty_zf = """$ORIGIN bar.id
$TTL 3600
pubkey TXT "pubkey:data:0"
registrar URI 10 1 "bsreg://foo.com:8234"
"""

        zf_json = zonefile.decode_name_zonefile(domain_name, empty_zf)
        self.assertEqual(zf_json['$origin'], domain_name)

        # bad transition n=0 -> n=0
        sub1 = subdomains.Subdomain("foo", domain_name, subdomains.encode_pubkey_entry(foo_bar_sk), 0, "")

        subdomain_util._extend_with_subdomain(zf_json, sub1)

        history.append(ysi_zones.make_zone_file(zf_json))

        # bad transition bad sig.
        zf_json = zonefile.decode_name_zonefile(domain_name, empty_zf)
        self.assertEqual(zf_json['$origin'], domain_name)

        sub2 = subdomains.Subdomain("foo", domain_name, subdomains.encode_pubkey_entry(bar_bar_sk), 1, "")
        subdomain_util._extend_with_subdomain(zf_json, sub2)
        history.append(ysi_zones.make_zone_file(zf_json))

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(1)], history[:1])
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertNotIn("bar.bar.id", subdomain_db)

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(2)], history[:2])
        self.assertIn("bar.bar.id", subdomain_db)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 0)

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(3)], history[:3])
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 0)

        # handle repeated zonefile

        subdomain_db = subdomains._build_subdomain_db(["bar.id" for x in range(3)], history[:3])
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 0)
        subdomains._build_subdomain_db(["bar.id" for x in range(3)], history[:3], subdomain_db = subdomain_db)
        self.assertEqual(subdomain_db["foo.bar.id"].n, 0)
        self.assertEqual(subdomain_db["bar.bar.id"].n, 0)        

    def test_large_zonefile(self):
        empty_zf = """$ORIGIN registrar.id
        $TTL 3600
        pubkey TXT "pubkey:data:0"
        registrar URI 10 1 "bsreg://foo.com:8234"
        """
        domain_name = "registrar.id"
        zf_js = zonefile.decode_name_zonefile(domain_name, empty_zf)
        #for i in range(0, 200):


if __name__ == '__main__':
    unittest.main()
