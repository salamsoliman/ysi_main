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
import ysi_client
import ysi_zones
import os
import sys
import subprocess
import keylib
import shutil
import ysi

wallets = [
    testlib.Wallet( "5JesPiN68qt44Hc2nT8qmyZ1JDwHebfoh9KQ52Lazb1m1LaKNj9", 100000000000 ),
    testlib.Wallet( "5KHqsiU9qa77frZb6hQy9ocV7Sus9RWJcQGYYBJJBb2Efj1o77e", 100000000000 ),
    testlib.Wallet( "5Kg5kJbQHvk1B64rJniEmgbD83FpZpbw2RjdAZEzTefs9ihN3Bz", 100000000000 ),
    testlib.Wallet( "5JuVsoS9NauksSkqEjbUZxWwgGDQbMwPsEfoRBSpLpgDX1RtLX7", 100000000000 ),
    testlib.Wallet( "5KEpiSRr1BrT8vRD7LKGCEmudokTh1iMHbiThMQpLdwBwhDJB1T", 100000000000 )
]

consensus = "17ac43c1d8549c3181b200f1bf97eb7d"
value_hashes = []

def take_snapshot(config_path, virtualchain_dir, snapshot_dir, max_age):
    """
    use ysi-snapshots to take a snapshot
    """
    cmd = "ysi-snapshots snapshot --config_file '{}' --snapshots '{}' --working_dir '{}' --debug --max_age '{}'".format(
            config_path, snapshot_dir, virtualchain_dir, max_age)

    print ''
    print '$ {}'.format(cmd)
    print ''
    
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate()
    exitcode = p.returncode

    if exitcode != 0:
        print 'exit code {}: {}'.format(exitcode, cmd)
        return False

    return True


def restore( snapshot_path, restore_dir, pubkeys, num_required ):
    
    global value_hashes

    config_path = os.environ.get("BLOCKSTACK_CLIENT_CONFIG")
    assert config_path

    os.makedirs(restore_dir)
    shutil.copy(config_path, os.path.join(restore_dir, os.path.basename(config_path)))

    rc = ysi.fast_sync_import( restore_dir, "file://{}".format(snapshot_path), public_keys=pubkeys, num_required=num_required )
    if not rc:
        print "failed to restore snapshot {}".format(snapshot_path)
        return False

    # database must be identical 
    db_filenames = ['ysi-server.db', 'ysi-server.snapshots', 'ysi-server.lastblock']
    src_paths = [os.path.join(virtualchain.get_working_dir(), fn) for fn in db_filenames]
    backup_paths = [os.path.join(restore_dir, fn) for fn in db_filenames]

    for src_path, backup_path in zip(src_paths, backup_paths):
        rc = os.system("cmp '{}' '{}'".format(src_path, backup_path))
        if rc != 0:
            print '{} disagress with {}'.format(src_path, backup_path)
            return False
    
    # all zone files must be present
    for vh in value_hashes:
        zfdata = ysi.get_cached_zonefile_data(vh, zonefile_dir=os.path.join(restore_dir, 'zonefiles'))
        if zfdata is None:
            print 'Missing {} in {}'.format(vh, os.path.join(restore_dir, 'zonefiles'))
            return False

    shutil.rmtree(restore_dir)
    return True


def scenario( wallets, **kw ):
    global value_hashes

    virtualchain_dir = os.environ.get('VIRTUALCHAIN_WORKING_DIR', None)
    assert virtualchain_dir

    privkey = keylib.ECPrivateKey(wallets[4].privkey).to_hex()
    config_file = os.path.join(virtualchain_dir, 'snapshots.ini')
    privkey_path = os.path.join(virtualchain_dir, 'snapshots.pkey')
    snapshot_dir = os.path.join(virtualchain_dir, 'snapshots')

    with open(privkey_path, 'w') as f:
        f.write(privkey)

    with open(config_file, 'w') as f:
        f.write("""
[ysi-snapshots]
private_key = {}
logfile = {}
""".format(privkey_path, os.path.join(virtualchain_dir, 'snapshots.log')))

    testlib.ysi_namespace_preorder( "test", wallets[1].addr, wallets[0].privkey )
    testlib.next_block( **kw )
    
    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 3)

    testlib.ysi_namespace_reveal( "test", wallets[1].addr, 52595, 250, 4, [6,5,4,3,2,1,0,0,0,0,0,0,0,0,0,0], 10, 10, wallets[0].privkey )
    testlib.next_block( **kw )
    
    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 3)

    testlib.ysi_namespace_ready( "test", wallets[1].privkey )
    testlib.next_block( **kw )
    
    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 3)

    testlib.ysi_name_preorder( "foo.test", wallets[2].privkey, wallets[3].addr )
    testlib.next_block( **kw )

    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 3)

    testlib.ysi_name_register( "foo.test", wallets[2].privkey, wallets[3].addr )
    testlib.next_block( **kw )

    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 3)

    zonefile = ysi_client.zonefile.make_empty_zonefile( "foo.test", wallets[0].pubkey_hex )
    zonefile_txt = ysi_zones.make_zone_file( zonefile )
    zonefile_hash = ysi_client.storage.get_zonefile_data_hash( zonefile_txt )
 
    value_hashes.append(zonefile_hash)

    assert ysi_client.storage.put_immutable_data( zonefile_txt, '00' * 32, data_hash=zonefile_hash )
    
    testlib.ysi_name_update('foo.test', zonefile_hash, wallets[3].privkey)
    testlib.next_block( **kw )

    # there must be three snapshots 
    res = os.listdir(snapshot_dir)
    assert len(res) == 4
    assert 'snapshot.bsk' in res

    assert take_snapshot(config_file, virtualchain_dir, snapshot_dir, 1)

    # now there's only one 
    res = os.listdir(snapshot_dir)
    assert len(res) == 2
    assert 'snapshot.bsk' in res

    # restore it
    restore_dir = os.path.join(snapshot_dir, 'test_restore')
    res = restore(os.path.join(snapshot_dir, 'snapshot.bsk'), restore_dir, [wallets[4].pubkey_hex], 1)
    assert res


def check( state_engine ):

    # not revealed, but ready 
    ns = state_engine.get_namespace_reveal( "test" )
    if ns is not None:
        print "namespace reveal exists"
        return False 

    ns = state_engine.get_namespace( "test" )
    if ns is None:
        print "no namespace"
        return False 

    if ns['namespace_id'] != 'test':
        print "wrong namespace"
        return False 

    # not preordered
    preorder = state_engine.get_name_preorder( "foo.test", virtualchain.make_payment_script(wallets[2].addr), wallets[3].addr )
    if preorder is not None:
        print "preorder exists"
        return False
    
    # registered 
    name_rec = state_engine.get_name( "foo.test" )
    if name_rec is None:
        print "name does not exist"
        return False 

    # owned by
    if name_rec['address'] != wallets[3].addr or name_rec['sender'] != virtualchain.make_payment_script(wallets[3].addr):
        print "sender is wrong"
        return False 

    return True
