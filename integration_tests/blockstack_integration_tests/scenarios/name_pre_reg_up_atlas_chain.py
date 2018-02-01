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
import time
import ysi_client
import ysi_zones
import virtualchain
import os
import sys

"""
TEST ENV BLOCKSTACK_ATLAS_NUM_NEIGHBORS 10
"""

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 ),
    testlib.Wallet( "5KaSTdRgMfHLxSKsiWhF83tdhEj2hqugxdBNPUAw5NU8DMyBJji", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
synchronized = False
value_hash = None

def scenario( wallets, **kw ):

    global synchronized, value_hash

    import ysi_integration_tests.atlas_network as atlas_network

    testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )

    testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )

    # set up RPC daemon
    test_proxy = testlib.TestAPIProxy()
    ysi_client.set_default_proxy( test_proxy )
    wallet_keys = ysi_client.make_wallet_keys( owner_privkey=wallets[3].privkey, data_privkey=wallets[4].privkey, payment_privkey=wallets[5].privkey )
    testlib.ysi_client_set_wallet( "0123456789abcdef", wallet_keys['payment_privkey'], wallet_keys['owner_privkey'], wallet_keys['data_privkey'] )

    # register 10 names
    for i in xrange(0, 10):
        res = testlib.ysi_name_preorder( "foo_{}.test".format(i), wallets[2].privkey, wallets[3].addr )
        if 'error' in res:
            print json.dumps(res)
            return False

    testlib.next_block( **kw )

    for i in xrange(0, 10):
        res = testlib.ysi_name_register( "foo_{}.test".format(i), wallets[2].privkey, wallets[3].addr )
        if 'error' in res:
            print json.dumps(res)
            return False

    testlib.next_block( **kw )

    # start up an Atlas test network with 9 nodes: the main one doing the test, and 8 subordinate ones that treat it as a seed peer
    # organize nodes into a linear chain: node n is neighbor to n-1 and n+1, with the seed at one end.
    # nodes cannot talk to anyone else.
    atlas_nodes = [17000, 17001, 17002, 17003, 17004, 17005, 17006, 17007]
    atlas_topology = {}

    atlas_topology[17000] = [16264, 17001]
    atlas_topology[17007] = [17006]

    for i in xrange(1, len(atlas_nodes)-1):
        atlas_topology[atlas_nodes[i]] = [atlas_nodes[i-1], atlas_nodes[i+1]]

    def chain_drop(src_hostport, dest_hostport):
        if src_hostport is None:
            return 0.0

        src_host, src_port = ysi_client.utils.url_to_host_port( src_hostport )
        dest_host, dest_port = ysi_client.utils.url_to_host_port( dest_hostport )

        if (src_port == 16264 and dest_port == 17000) or (src_port == 17000 and dest_port == 16264):
            # seed end of the chain
            return 0.0

        if abs(src_port - dest_port) <= 1:
            # chain link
            return 0.0

        # drop otherwise
        return 1.0

    network_des = atlas_network.atlas_network_build( atlas_nodes, atlas_topology, {}, os.path.join( testlib.working_dir(**kw), "atlas_network" ) )
    atlas_network.atlas_network_start( network_des, drop_probability=chain_drop )

    print "Waiting 25 seconds for the altas peers to catch up"
    time.sleep(25.0)

    # make 10 empty zonefiles and propagate them
    for i in xrange(0, 10):
        data_pubkey = virtualchain.BitcoinPrivateKey(wallet_keys['data_privkey']).public_key().to_hex()
        empty_zonefile = ysi_client.zonefile.make_empty_zonefile( "foo_{}.test".format(i), data_pubkey, urls=["file:///tmp/foo_{}.test".format(i)] )
        empty_zonefile_str = ysi_zones.make_zone_file( empty_zonefile )
        value_hash = ysi_client.hash_zonefile( empty_zonefile )

        res = testlib.ysi_name_update( "foo_{}.test".format(i), value_hash, wallets[3].privkey )
        if 'error' in res:
            print json.dumps(res)
            return False

        testlib.next_block( **kw )

        # propagate
        res = testlib.ysi_cli_sync_zonefile('foo_{}.test'.format(i), zonefile_string=empty_zonefile_str)
        if 'error' in res:
            print json.dumps(res)
            return False

    # wait at most 60 seconds for atlas network to converge
    synchronized = False
    for i in xrange(0, 60):
        atlas_network.atlas_print_network_state( network_des )
        if atlas_network.atlas_network_is_synchronized( network_des, testlib.last_block( **kw ) - 1, 1 ):
            print "Synchronized!"
            sys.stdout.flush()
            synchronized = True
            break

        else:
            time.sleep(1.0)

    # shut down
    atlas_network.atlas_network_stop( network_des )
    if not synchronized:
        print "Not synchronized"
        sys.stdout.flush()

    return synchronized


def check( state_engine ):

    global synchronized
    if not synchronized:
        print "not synchronized"
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

    for i in xrange(0, 10):
        name = 'foo_{}.test'.format(i)
        # not preordered
        preorder = state_engine.get_name_preorder( name, virtualchain.make_payment_script(wallets[2].addr), wallets[3].addr )
        if preorder is not None:
            print "still have preorder"
            return False

        # registered
        name_rec = state_engine.get_name( name )
        if name_rec is None:
            print "name does not exist"
            return False

        # owned
        if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
            print "name has wrong owner"
            return False

        # updated
        if name_rec['value_hash'] is None:
            print "wrong value hash: %s" % name_rec['value_hash']
            return False

    return True
