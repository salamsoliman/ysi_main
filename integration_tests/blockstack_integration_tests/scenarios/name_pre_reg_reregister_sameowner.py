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

# in epoch 2 immediately, but with the old price (in order to test compatibility with 0.13)
"""
TEST ENV BLOCKSTACK_EPOCH_1_END_BLOCK 682
TEST ENV BLOCKSTACK_EPOCH_2_PRICE_MULTIPLIER 1.0
"""
wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
last_first_block = None
first_preorder = None

def scenario( wallets, **kw ):

    global last_first_block, first_preorder 

    testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_reveal( "test", wallets[1].addr, 1, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    # preorder, register, expire (multiple times)
    for i in xrange(2, 5):
        resp = testlib.ysi_name_preorder( "foo.test", wallets[2].privkey, wallets[3].addr, safety_checks=False )
        if 'error' in resp:
            print json.dumps( resp, indent=4 )

        testlib.next_block( **kw )
    
        if first_preorder is None:
            first_preorder = testlib.get_current_block( **kw )

        resp = testlib.ysi_name_register( "foo.test", wallets[2].privkey, wallets[3].addr, safety_checks=False )
        if 'error' in resp:
            print json.dumps( resp, indent=4 )

        testlib.next_block( **kw )
        
        last_first_block = testlib.get_current_block( **kw )

        if i == 4:
            break

        testlib.next_block( **kw )
        testlib.next_block( **kw )


def check( state_engine ):

    global last_first_block, first_preorder

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        return False 

    if ns['namespace_id'] != 'test':
        return False 

    # not preordered
    preorder = state_engine.get_name_preorder( "foo.test", virtualchain.make_payment_script(wallets[2].addr), wallets[3].addr )
    if preorder is not None:
        print json.dumps(name_rec, indent=4)
        return False
    
    # registered to new owner
    name_rec = state_engine.get_name( "foo.test" )
    if name_rec is None:
        print "name rec is None"
        return False 

    if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
        print json.dumps(name_rec, indent=4 )
        return False

    # check blocks 
    if name_rec['first_registered'] != last_first_block:
        print "wrong first_registered; expected %s" % last_first_block
        print json.dumps(name_rec, indent=4, sort_keys=True )
        return False 

    if name_rec['block_number'] != first_preorder:
        print "wrong block_number; expected %s" % last_first_preorder
        print json.dumps(name_rec, indent=4, sort_keys=True)
        return False


    return True

