#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    Blockstack
    ~~~~~
    copyright: (c) 2014-2015 by Halfmoon Labs, Inc.
    copyright: (c) 2016 by Blockstack.org

    This file is part of Blockstack

    Blockstack is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Blockstack is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with Blockstack. If not, see <http://www.gnu.org/licenses/>.
""" 
import os
import testlib
import virtualchain
import urllib2
import json
import ysi_client
import ysi_profiles
import sys
import keylib
from keylib import ECPrivateKey, ECPublicKey

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 ),
    testlib.Wallet( "5K5hDuynZ6EQrZ4efrchCwy6DLhdsEzuJtTDAf3hqdsCKbxfoeD", 100000000000 ),
    testlib.Wallet( "5J39aXEeHh9LwfQ4Gy5Vieo7sbqiUMBXkPH7SaMHixJhSSBpAqz", 100000000000 ),
    testlib.Wallet( "5K9LmMQskQ9jP1p7dyieLDAeB6vsAj4GK8dmGNJAXS1qHDqnWhP", 100000000000 ),
    testlib.Wallet( "5KcNen67ERBuvz2f649t9F2o1ddTjC5pVUEqcMtbxNgHqgxG2gZ", 100000000000 ),
    testlib.Wallet( "5KMbNjgZt29V6VNbcAmebaUT2CZMxqSridtM46jv4NkKTP8DHdV", 100000000000 ),
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
wallet_keys = None
wallet_keys_2 = None
error = False

index_file_data = "<html><head></head><body>foo.test hello world</body></html>"
resource_data = "hello world"

def scenario( wallets, **kw ):

    global wallet_keys, wallet_keys_2, error, index_file_data, resource_data

    wallet_keys = testlib.ysi_client_initialize_wallet( "0123456789abcdef", wallets[5].privkey, wallets[3].privkey, wallets[4].privkey )
    wallet_keys_2 = testlib.ysi_client_initialize_wallet( "0123456789abcdef", wallets[9].privkey, wallets[7].privkey, wallets[8].privkey )

    test_proxy = testlib.TestAPIProxy()
    ysi_client.set_default_proxy( test_proxy )

    testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    testlib.ysi_name_preorder( "foo.test", wallets[2].privkey, wallets[3].addr )
    testlib.ysi_name_preorder( "bar.test", wallets[6].privkey, wallets[7].addr )
    testlib.next_block( **kw )
    
    testlib.ysi_name_register( "foo.test", wallets[2].privkey, wallets[3].addr )
    testlib.ysi_name_register( "bar.test", wallets[6].privkey, wallets[7].addr )
    testlib.next_block( **kw )

    # migrate profiles 
    res = testlib.migrate_profile( "foo.test", proxy=test_proxy, wallet_keys=wallet_keys )
    if 'error' in res:
        res['test'] = 'Failed to initialize foo.test profile'
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    res = testlib.migrate_profile( "bar.test", proxy=test_proxy, wallet_keys=wallet_keys_2 )
    if 'error' in res:
        res['test'] = 'Failed to initialize bar.test profile'
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    # tell serialization-checker that value_hash can be ignored here
    print "BLOCKSTACK_SERIALIZATION_CHECK_IGNORE value_hash"
    sys.stdout.flush()
    
    testlib.next_block( **kw )
 
    res = testlib.start_api("0123456789abcdef")
    if 'error' in res:
        print 'failed to start API: {}'.format(res)
        return False

    data_pk = wallets[-1].privkey
    data_pub = wallets[-1].pubkey_hex
    
    config_path = os.environ.get("BLOCKSTACK_CLIENT_CONFIG", None)

    # make an index file 
    index_file_path = "/tmp/name_preorder_register_update_app_auth.foo.test.index.html"
    with open(index_file_path, "w") as f:
        f.write(index_file_data)

    testlib.ysi_client_set_wallet( "0123456789abcdef", wallets[5].privkey, wallets[3].privkey, wallets[4].privkey )
 
    res = testlib.start_api("0123456789abcdef")
    if 'error' in res:
        print 'failed to start API: {}'.format(res)
        return False

    # register an application under foo.test
    res = testlib.ysi_cli_app_publish("foo.test", "ping.app", "node_read", index_file_path, password="0123456789abcdef" )
    if 'error' in res:
        res['test'] = 'Failed to register foo.test/bar app'
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    # activate bar.test
    testlib.ysi_client_set_wallet( "0123456789abcdef", wallets[9].privkey, wallets[7].privkey, wallets[8].privkey )
 
    res = testlib.start_api("0123456789abcdef")
    if 'error' in res:
        print 'failed to start API: {}'.format(res)
        return False

    # sign in 
    pk = 'ce100586279d3b127b7dcc137fcc2f18b272bb2b43bdaea3584d0ea17087ec0201'
    pubk = keylib.ECPrivateKey(pk).public_key().to_hex()
    res = testlib.ysi_cli_app_signin("foo.test", pk, "ping.app", ["node_read"])
    if 'error' in res:
        res['test'] = 'Failed to signin: {}'.format(res['error'])
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    ses = res['token']

    res = testlib.ysi_REST_call("GET", "/v1/ping", ses)
    if res['http_status'] != 200:
        print "failed to GET /api/v1/ping"
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return False

    if res['response']['status'] != 'alive':
        print "failed to GET /api/v1/ping"
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return False
   
    # access index.html 
    res = testlib.ysi_REST_call("GET", "/v1/resources/foo.test/ping.app?name=index.html&pubkey={}".format(wallets[4].pubkey_hex), ses)
    if 'error' in res or res['http_status'] != 200:
        print 'failed to GET /v1/resources?name=/index.html'
        print json.dumps(res)
        error = True
        return False

    if res['raw'] != index_file_data:
        print 'expected {}\ngot {}\n'.format(index_file_data, res['raw'])
        print json.dumps(res)
        error = True
        return False

    testlib.next_block( **kw )



def check( state_engine ):

    global wallet_keys, error, index_file_data, resource_data
    
    config_path = os.environ.get("BLOCKSTACK_CLIENT_CONFIG")
    assert config_path

    if error:
        print "Key operation failed."
        return False

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        print "namespace not ready"
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        print "no namespace"
        return False 

    if ns['namespace_id'] != 'test':
        print "wrong namespace"
        return False 

    names = ['foo.test', 'bar.test']
    wallet_keys_list = [wallet_keys, wallet_keys_2]
    test_proxy = testlib.TestAPIProxy()

    for i in xrange(0, len(names)):
        name = names[i]
        wallet_payer = 3 * (i+1) - 1 + i
        wallet_owner = 3 * (i+1) + i
        wallet_data_pubkey = 3 * (i+1) + 1 + i
        wallet_keys = wallet_keys_list[i]

        # not preordered
        preorder = state_engine.get_name_preorder( name, virtualchain.make_payment_script(wallets[wallet_payer].addr), wallets[wallet_owner].addr )
        if preorder is not None:
            print "still have preorder"
            return False
    
        # registered 
        name_rec = state_engine.get_name( name )
        if name_rec is None:
            print "name does not exist"
            return False 

        # owned 
        if name_rec['address'] != wallets[wallet_owner].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[wallet_owner].addr):
            print "name {} has wrong owner".format(name)
            return False 

    # get app config 
    app_config = testlib.ysi_cli_app_get_config( "foo.test", "ping.app" )
    if 'error' in app_config:
        print "failed to get app config\n{}\n".format(json.dumps(app_config, indent=4, sort_keys=True))
        return False

    # inspect...
    app_config = app_config['config']
    print json.dumps(app_config, indent=4, sort_keys=True)

    if app_config['driver_hints'] != []:
        print "Invalid driver hints\n{}\n".format(json.dumps(app_config, indent=4, sort_keys=True))
        return False

    if app_config['api_methods'] != ['node_read']:
        print "Invalid API list\n{}\n".format(json.dumps(app_config, indent=4, sort_keys=True))
        return False

    if len(app_config['index_uris']) != 1:
        print "Invalid URI records\n{}\n".format(json.dumps(app_config, indent=4, sort_keys=True))
        return False

    if app_config['blockchain_id'] != 'foo.test':
        print "invalid blockchain ID\n{}\n".format(app_config)
        return False

    return True
