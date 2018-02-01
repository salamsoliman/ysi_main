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

# change epochs
import os

"""
TEST ENV BLOCKSTACK_EPOCH_1_END_BLOCK 694
TEST ENV BLOCKSTACK_EPOCH_2_END_BLOCK 696
TEST ENV BLOCKSTACK_EPOCH_2_NAMESPACE_LIFETIME_MULTIPLIER 2
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_MULTIPLIER 2
TEST ENV BLOCKSTACK_EPOCH_3_NAMESPACE_LIFETIME_GRACE_PERIOD 5
"""

import testlib
import virtualchain
import json
import shutil
import tempfile

import ysi

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
first_name_block = None

def scenario( wallets, **kw ):

    global first_name_block

    # make a test namespace
    resp = testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    if 'error' in resp:
        print json.dumps( resp, indent=4 )
        return False

    testlib.next_block( **kw ) # 689

    resp = testlib.ysi_namespace_reveal( "test", wallets[1].addr, 2, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    if 'error' in resp:
        print json.dumps( resp, indent=4 )
        return False

    testlib.next_block( **kw ) # 690

    resp = testlib.ysi_name_import( "foo.test", wallets[3].addr, "11" * 20, wallets[1].privkey )
    if 'error' in resp:
        print json.dumps( resp, indent=4 )
        return False

    testlib.next_block( **kw ) # 691
    first_name_block = testlib.get_current_block( **kw )

    resp = testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    if 'error' in resp:
        print json.dumps( resp, indent=4 )
        return False

    testlib.next_block( **kw ) # 692
    testlib.next_block( **kw ) # end of 693

    whois = testlib.ysi_cli_whois('foo.test')
    if 'error' in whois:
        print 'failed to whois foo.test'
        print json.dumps(whois, indent=4)
        return False

    # this should be the penultimate block
    if whois['expire_block'] != testlib.get_current_block(**kw) + 1:
        print 'wrong expire block (got {}, expected {})'.format(whois['expire_block'], testlib.get_current_block(**kw))
        print whois
        return False

    resp = testlib.ysi_name_renew( 'foo.test', wallets[3].privkey )
    if 'error' in resp:
        print json.dumps(resp, indent=4 )
        return False

    testlib.next_block( **kw ) # end of 694 (epoch 2 is now active)
    testlib.next_block( **kw ) # 695

    whois = testlib.ysi_cli_whois( 'foo.test' )
    if 'error' in whois:
        print whois
        return False

    if whois['expire_block'] != testlib.get_current_block(**kw) + 3:
        print 'wrong expire block: {} != {} + 3'.format(whois['expire_block'], testlib.get_current_block(**kw))
        return False

    testlib.next_block( **kw ) # end of 696 (epoch 3 is now active)
    
    whois = testlib.ysi_cli_whois( 'foo.test' )
    if 'error' in whois:
        print whois
        return False
    
    if whois['expire_block'] != testlib.get_current_block(**kw) + 2:
        print 'wrong expire block: {} != {} + 2'.format(whois['expire_block'], testlib.get_current_block(**kw))
        return False

    testlib.next_block( **kw ) # 697
    
    whois = testlib.ysi_cli_whois( 'foo.test' )
    if 'error' in whois:
        print whois
        return False
    
    if whois['expire_block'] != testlib.get_current_block(**kw) + 1:
        print 'wrong expire block: {} != {} + 1'.format(whois['expire_block'], testlib.get_current_block(**kw))
        return False

    testlib.next_block( **kw ) # 698 

    if whois['expire_block'] != testlib.get_current_block(**kw):
        print 'wrong expire block: {} != {}'.format(whois['expire_block'], testlib.get_current_block(**kw))
        return False

    testlib.next_block( **kw ) # end of 699 (expired now)
    testlib.next_block( **kw ) # 700
    testlib.next_block( **kw ) # 701
    testlib.next_block( **kw ) # 702

    resp = testlib.ysi_name_renew( 'foo.test', wallets[3].privkey, zonefile_hash='22'*20, recipient_addr=wallets[2].addr)
    if 'error' in resp:
        print resp
        return False

    testlib.next_block(**kw) # 703

    whois = testlib.ysi_cli_whois('foo.test')
    if 'error' in whois:
        print whois
        return False

    if whois['expire_block'] != testlib.get_current_block(**kw) + 4:
        print 'expire block: {}'.format(whois['expire_block'])
        print 'current block + 4: {}'.format(testlib.get_current_block(**kw) + 4)
        return False

    if whois['renewal_deadline'] != testlib.get_current_block(**kw) + 9:
        print 'renewal deadline: {}'.format(whois['renewal_deadline'])
        print 'current block + 9: {}'.format(testlib.get_current_block(**kw) + 9)
        return False


def check( state_engine ):

    global first_name_block 

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
    for i in xrange(0, len(wallets)):
        preorder = state_engine.get_name_preorder( "foo.test", virtualchain.make_payment_script(wallets[i].addr), wallets[(i+1)%5].addr )
        if preorder is not None:
            print "preordered"
            return False

    # registered 
    name_rec = state_engine.get_name( "foo.test" )
    if name_rec is None:
        print "no name"
        return False 

    # renewed (12 blocks later, starting from renewal time)
    if name_rec['last_renewed'] - 12 != name_rec['first_registered']:
        print name_rec['last_renewed']
        print name_rec['first_registered']
        return False

    namespace_rec = state_engine.get_namespace("test")
    if namespace_rec is None:
        print "missing namespace"
        return False

    # renewal fee should have been name_cost * epoch_cost_multiplier
    # make sure we have both the original and new prices
    original_price = 6400000
    historic_name_rec = state_engine.get_name_at( "foo.test", first_name_block )
    if historic_name_rec is None or len(historic_name_rec) == 0:
        print "missing historic name rec at %s" % first_name_rec
        return False

    historic_name_rec = historic_name_rec[0]

    if abs(original_price - historic_name_rec['op_fee']) >= 10e-8:
        print "historic op fee mismatch: original price = %s, historic fee = %s" % (original_price, historic_name_rec['op_fee'])
        return False

    current_fee = original_price * ysi.lib.config.get_epoch_price_multiplier( 703, "test" )
    current_price = ysi.price_name( "foo", namespace_rec, 703 )

    if abs(current_price - current_fee) >= 10e-8:
        print "current op fee mismatch: original price = %s, historic price = %s" % (current_price, current_fee)
        return False

    epoch_cost_multiplier = ysi.get_epoch_price_multiplier( 703, "test" )

    if abs(original_price * epoch_cost_multiplier - current_price) >= 10e-8:
        print "epoch cost failure: original_price = %s, multiplier = %s, current price = %s" % (original_price, epoch_cost_multiplier, current_price)
        return False

    return True
