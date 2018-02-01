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

import testlib
import virtualchain
import json
import shutil
import tempfile
import os
import keychain
import virtualchain

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 ),
    testlib.Wallet( "5K5hDuynZ6EQrZ4efrchCwy6DLhdsEzuJtTDAf3hqdsCKbxfoeD", 100000000000 ),
    testlib.Wallet( "5J39aXEeHh9LwfQ4Gy5Vieo7sbqiUMBXkPH7SaMHixJhSSBpAqz", 100000000000 ),
    testlib.Wallet( "5K9LmMQskQ9jP1p7dyieLDAeB6vsAj4GK8dmGNJAXS1qHDqnWhP", 100000000000 ),
    testlib.Wallet( "5KcNen67ERBuvz2f649t9F2o1ddTjC5pVUEqcMtbxNgHqgxG2gZ", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"

debug = True

def scenario( wallets, **kw ):

    # make a test namespace
    resp = testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    if debug or 'error' in resp:
        print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )

    resp = testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    if debug or 'error' in resp:
        print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )
    
    # import 3 names in the same block: foo.test, bar.test, baz.test
    names = ['foo.test', 'bar.test', 'baz.test']
    name_preorder_wallets = [wallets[2], wallets[3], wallets[4]]
    name_register_wallets = [wallets[5], wallets[6], wallets[7]]
    name_transfer_wallets = [wallets[6], wallets[7], wallets[5]]

    # derive importer keys and do imports
    # NOTE: breaks consensus trace from 0.14.0
    private_keychain = keychain.PrivateKeychain.from_private_key( wallets[1].privkey )
    private_keys = [wallets[1].privkey]     # NOTE: always start with the reveal key, then use children
    for i in xrange(0, len(names)-1):
        import_key = private_keychain.child(i).private_key()

        print "fund {} (child {})".format(import_key, i)
        res = testlib.send_funds( wallets[1].privkey, 100000000, virtualchain.BitcoinPrivateKey(import_key).public_key().address() )
        if 'error' in res:
            print json.dumps(res, indent=4, sort_keys=True)
            return False

        testlib.next_block(**kw)
        private_keys.append(import_key)


    for i in xrange(0, len(names)):

        name = names[i]
        register_wallet = name_register_wallets[i]
        import_key = private_keys[i]

        resp = testlib.ysi_name_import( name, register_wallet.addr, str(9 - i) * 40, import_key, safety_checks=False )
        if debug or  'error' in resp:
            print json.dumps( resp, indent=4 )

   
    testlib.next_block( **kw )

    # namespace ready...
    resp = testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    if debug or  'error' in resp:
        print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )

    # update 3 names in the same block
    for i in xrange(0, len(names)):

        name = names[i]
        register_wallet = name_register_wallets[i]

        resp = testlib.ysi_name_update( name, str(i + 2) * 40, register_wallet.privkey )
        if debug or  'error' in resp:
            print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )

    # update 3 names in the same block, again
    for i in xrange(0, len(names)):

        name = names[i]
        register_wallet = name_register_wallets[i]

        resp = testlib.ysi_name_update( name, str(i + 1) * 40, register_wallet.privkey )
        if debug or  'error' in resp:
            print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )

    # transfer 3 names in the same block 
    for i in xrange(0, len(names)):

        name = names[i]
        register_wallet = name_register_wallets[i]
        transfer_wallet = name_transfer_wallets[i]

        resp = testlib.ysi_name_transfer( name, transfer_wallet.addr, True, register_wallet.privkey ) 
        if debug or  'error' in resp:
            print json.dumps( resp, indent=4 )

    testlib.next_block( **kw )

    # exchange after transfer...
    tmp = name_register_wallets
    name_register_wallets = name_transfer_wallets
    name_transfer_wallets = tmp

    # revoke 3 names in the same block 
    for i in xrange(0, len(names)):

        name = names[i]
        register_wallet = name_register_wallets[i]

        resp = testlib.ysi_name_revoke( name, register_wallet.privkey )
        if debug or 'error' in resp:
            print json.dumps( resp, indent=4 )

    # iterate the blocks a few times 
    for i in xrange(0, 5):
        testlib.next_block( **kw )


def check( state_engine ):

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        return False 

    if ns['namespace_id'] != 'test':
        return False 

    names = ['foo.test', 'bar.test', 'baz.test']
    name_preorder_wallets = [wallets[2], wallets[3], wallets[4]]
    name_register_wallets = [wallets[5], wallets[6], wallets[7]]
    name_transfer_wallets = [wallets[6], wallets[7], wallets[5]]

    for i in xrange(0, len(names)):

        name = names[i]
        name_preorder_wallet = name_preorder_wallets[i]
        name_register_wallet = name_register_wallets[i]
        name_transfer_wallet = name_transfer_wallets[i]

        # not preordered
        preorder = state_engine.get_name_preorder( name, virtualchain.make_payment_script(name_preorder_wallet.addr), name_register_wallet.addr )
        if preorder is not None:
            print "%s still preordered" % name
            return False
        
        # registered 
        name_rec = state_engine.get_name( name )
        if name_rec is None:
            print "not registered %s" % name
            return False 

        # updated, and data is gone (since revoked)
        if name_rec['value_hash'] is not None:
            print "invalid value hash %s: %s" % (name, name_rec['value_hash'])
            return False 

        # owned by the right transfer wallet 
        if name_rec['address'] != name_transfer_wallet.addr or name_rec['sender'] != virtualchain.make_payment_script(name_transfer_wallet.addr):
            print "%s owned by %s" % (name, name_transfer_wallet.addr)
            return False

        # revoked 
        if not name_rec['revoked']:
            print "%s not revoked" % name
            return False 

    return True
