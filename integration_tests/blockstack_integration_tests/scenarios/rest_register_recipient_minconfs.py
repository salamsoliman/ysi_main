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

# force 6 min confirmations by default
"""
TEST ENV BLOCKSTACK_MIN_CONFIRMATIONS 6
"""

import os
import testlib
import virtualchain
import urllib2
import json
import ysi_client
import ysi_profiles
import ysi_zones
import sys
import keylib
import time

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
    test_proxy = testlib.TestAPIProxy()
    ysi_client.set_default_proxy( test_proxy )

    testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )

    for i in xrange(0, 3):
        testlib.next_block( **kw )
    
    # try to preorder another namespace; it should fail
    res = testlib.ysi_namespace_preorder( "test2", wallets[1].addr, wallets[0].privkey )
    if 'error' not in res:
        print 'accidentally succeeded to preorder test2'
        return False

    # try to reveal; it should fail 
    res = testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    if 'error' not in res:
        print 'accidentally succeeded to reveal test'
        return False

    testlib.expect_snv_fail_at( "test2", testlib.get_current_block(**kw)+1)
    testlib.expect_snv_fail_at( "test", testlib.get_current_block(**kw)+1)

    for i in xrange(0, 3):
        testlib.next_block( **kw )

    # should succeed
    res = testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    if 'error' in res:
        print res
        return False

    for i in xrange(0, 3):
        testlib.next_block( **kw )

    # should fail, since we have an unusable address
    res = testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    if 'error' not in res:
        print res
        return False

    testlib.expect_snv_fail_at( "test", testlib.get_current_block(**kw)+1)

    for i in xrange(0, 3):
        testlib.next_block( **kw )

    # should work now
    res = testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    if 'error' in res:
        print res
        return False

    testlib.next_block( **kw )

    testlib.ysi_name_preorder( "foo.test", wallets[2].privkey, wallets[3].addr )
    
    for i in xrange(0, 3):
        testlib.next_block( **kw )
   
    # should fail to re-preorder, since address isn't ready
    res = testlib.ysi_name_preorder( "foo2.test", wallets[2].privkey, wallets[3].addr )
    if 'error' not in res:
        print 'accidentally succeeded to preorder foo2.test'
        return False

    testlib.expect_snv_fail_at( "foo2.test", testlib.get_current_block(**kw)+1)

    # should fail for the same reason: the payment address is not ready
    res = testlib.ysi_name_register( "foo.test", wallets[2].privkey, wallets[3].addr )
    if 'error' not in res:
        print 'accidentally succeeded to register foo.test'
        return False

    testlib.expect_snv_fail_at( "foo.test", testlib.get_current_block(**kw)+1)

    for i in xrange(0, 3):
        testlib.next_block( **kw )
    
    # should succeed now that it's confirmed
    res = testlib.ysi_name_register( "foo.test", wallets[2].privkey, wallets[3].addr )
    if 'error' in res:
        print res
        return False

    for i in xrange(0, 3):
        testlib.next_block( **kw )
    
    # should fail; address not ready
    res = testlib.migrate_profile( "foo.test", proxy=test_proxy, wallet_keys=wallet_keys )
    if 'error' not in res:
        print 'accidentally succeeded to migrate profile'
        return False

    testlib.expect_snv_fail_at( "foo.test", testlib.get_current_block(**kw)+1)

    for i in xrange(0, 3):
        testlib.next_block( **kw )
    
    # migrate profiles (should succeed now) 
    res = testlib.migrate_profile( "foo.test", proxy=test_proxy, wallet_keys=wallet_keys )
    if 'error' in res:
        res['test'] = 'Failed to initialize foo.test profile'
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    # tell serialization-checker that value_hash can be ignored here
    print "BLOCKSTACK_SERIALIZATION_CHECK_IGNORE value_hash"
    sys.stdout.flush()
    
    config_path = os.environ.get("BLOCKSTACK_CLIENT_CONFIG", None)

    # make a session 
    datastore_pk = keylib.ECPrivateKey(wallets[-1].privkey).to_hex()
    res = testlib.ysi_cli_app_signin("foo.test", datastore_pk, 'register.app', ['names', 'register', 'prices', 'zonefiles', 'blockchain', 'node_read', 'wallet_read'])
    if 'error' in res:
        print json.dumps(res, indent=4, sort_keys=True)
        error = True
        return 

    ses = res['token']
  
    # make zonefile for recipient
    driver_urls = ysi_client.storage.make_mutable_data_urls('bar.test', use_only=['dht', 'disk'])
    zonefile = ysi_client.zonefile.make_empty_zonefile('bar.test', wallets[4].pubkey_hex, urls=driver_urls)
    zonefile_txt = ysi_zones.make_zone_file( zonefile, origin='bar.test', ttl=3600 )

    # register the name bar.test (no zero-conf, should fail)
    res = testlib.ysi_REST_call('POST', '/v1/names', ses, data={'name': 'bar.test', 'zonefile': zonefile_txt, 'owner_address': wallets[4].addr})
    if res['http_status'] == 200:
        print 'accidentally succeeded to register bar.test'
        print res
        return False

    # let's test /v1/wallet/balance
    res = testlib.ysi_REST_call('GET', '/v1/wallet/balance', ses)
    if res['http_status'] != 200:
        print '/v1/wallet/balance returned ERR'
        print json.dumps(res)
        return False
    if res['response']['balance']['satoshis'] > 0:
        print '/v1/wallet/balance accidentally incorporated 0-conf txns in balance register bar.test'
        print json.dumps(res['response'])
        return False

    # let's test /v1/wallet/balance with minconfs=0
    res = testlib.ysi_REST_call('GET', '/v1/wallet/balance/0', ses)
    if res['http_status'] != 200:
        print '/v1/wallet/balance/0 returned ERR'
        print json.dumps(res)
        return False
    if res['response']['balance']['satoshis'] < 1e6:
        print "/v1/wallet/balance/0 didn't incorporate 0-conf txns"
        print json.dumps(res['response'])
        return False

    # register the name bar.test (1-conf, should fail)
    res = testlib.ysi_REST_call('POST', '/v1/names', ses, data={'name': 'bar.test', 'zonefile': zonefile_txt, 'owner_address': wallets[4].addr, 'min_confs' : 1})
    if res['http_status'] == 200:
        print 'accidentally succeeded to register bar.test'
        print res
        return False

    # register the name bar.test (zero-conf, should succeed)
    res = testlib.ysi_REST_call('POST', '/v1/names', ses, data={'name': 'bar.test', 'zonefile': zonefile_txt, 'owner_address': wallets[4].addr, 'min_confs': 0})
    if 'error' in res:
        res['test'] = 'Failed to register user'
        print json.dumps(res)
        error = True
        return False

    print res
    tx_hash = res['response']['transaction_hash']

    # wait for preorder to get confirmed...
    for i in xrange(0, 6):
        testlib.next_block( **kw )

    res = testlib.verify_in_queue(ses, 'bar.test', 'preorder', tx_hash )
    if not res:
        return False

    # wait for the preorder to get confirmed
    for i in xrange(0, 4):
        testlib.next_block( **kw )

    # wait for register to go through 
    print 'Wait for register to be submitted'
    time.sleep(10)

    # wait for the register to get confirmed 
    for i in xrange(0, 6):
        testlib.next_block( **kw )

    res = testlib.verify_in_queue(ses, 'bar.test', 'register', None )
    if not res:
        return False

    for i in xrange(0, 4):
        testlib.next_block( **kw )

    print 'Wait for update to be submitted'
    time.sleep(10)

    # wait for update to get confirmed 
    for i in xrange(0, 6):
        testlib.next_block( **kw )

    res = testlib.verify_in_queue(ses, 'bar.test', 'update', None )
    if not res:
        return False

    for i in xrange(0, 4):
        testlib.next_block( **kw )
  
    print 'Wait for transfer to be submitted'
    time.sleep(10)

    # wait for transfer to get confirmed 
    for i in xrange(0, 6):
        testlib.next_block( **kw )

    res = testlib.verify_in_queue(ses, 'bar.test', 'transfer', None )
    if not res:
        return False

    for i in xrange(0, 4):
        testlib.next_block( **kw )
  
    print 'Wait for transfer to be confirmed'
    time.sleep(10)

    res = testlib.ysi_REST_call("GET", "/v1/names/bar.test", ses)
    if 'error' in res or res['http_status'] != 200:
        res['test'] = 'Failed to get name bar.test'
        print json.dumps(res)
        return False

    zonefile_hash = res['response']['zonefile_hash']

    # should still be registered 
    if res['response']['status'] != 'registered':
        print "register not complete"
        print json.dumps(res)
        return False

    # do we have the history for the name?
    res = testlib.ysi_REST_call("GET", "/v1/names/bar.test/history", ses )
    if 'error' in res or res['http_status'] != 200:
        res['test'] = "Failed to get name history for foo.test"
        print json.dumps(res)
        return False

    # valid history?
    hist = res['response']
    if len(hist.keys()) != 4:
        res['test'] = 'Failed to get update history'
        res['history'] = hist
        print json.dumps(res, indent=4, sort_keys=True)
        return False

    # get the zonefile
    res = testlib.ysi_REST_call("GET", "/v1/names/bar.test/zonefile/{}".format(zonefile_hash), ses )
    if 'error' in res or res['http_status'] != 200:
        res['test'] = 'Failed to get name zonefile'
        print json.dumps(res)
        return False

    # same zonefile we put?
    if res['response']['zonefile'] != zonefile_txt:
        res['test'] = 'mismatched zonefile, expected\n{}\n'.format(zonefile_txt)
        print json.dumps(res)
        return False

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
    wallet_keys_list = [wallet_keys, wallet_keys]
    test_proxy = testlib.TestAPIProxy()

    for i in xrange(0, len(names)):
        name = names[i]
        wallet_payer = 5
        wallet_owner = 3 + i
        wallet_data_pubkey = 4

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

    return True
