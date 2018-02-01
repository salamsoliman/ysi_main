#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    Blockstack-client
    ~~~~~
    copyright: (c) 2014-2015 by Halfmoon Labs, Inc.
    copyright: (c) 2016 by Blockstack.org

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


from ..b40 import is_b40
from ..constants import (
    DEFAULT_DUST_FEE, DEFAULT_OP_RETURN_FEE,
    TX_MIN_CONFIRMATIONS, NAME_SCHEME,
    LENGTH_CONSENSUS_HASH, LENGTH_MAX_NAME)
from ..logger import get_logger

from ..scripts import (
    hash_name,
    hash256_trunc128,
    ysi_script_to_hex,
    add_magic_bytes,
    is_name_valid,
    tx_get_unspents,
    hash256_trunc128
)

import virtualchain
log = get_logger("ysi-client")


def build(name, script_pubkey, register_addr, consensus_hash, name_hash=None):
    """
    Takes a name, including the namespace ID (but not the id: scheme), a script_publickey to prove ownership
    of the subsequent NAME_REGISTER operation, and the current consensus hash for this block (to prove that the 
    caller is not on a shorter fork).
    
    Returns a NAME_PREORDER script.
    
    Record format:
    
    0     2  3                                              23             39
    |-----|--|----------------------------------------------|--------------|
    magic op  hash(name.ns_id,script_pubkey,register_addr)   consensus hash
    
    """
    
    if name_hash is None:

        # expect inputs to the hash
        if not is_b40( name ) or "+" in name or name.count(".") > 1:
           raise Exception("Name '%s' has non-base-38 characters" % name)
       
        '''
        # name itself cannot exceed maximum name length
        if len(NAME_SCHEME) + len(name) > LENGTH_MAX_NAME:
           raise Exception("Name '%s' is too long; exceeds %s bytes" % (name, LENGTH_MAX_NAME - len(NAME_SCHEME)))
        '''
        if not is_name_valid(name):
            raise Exception("Name {} is not valid".format(name))
    
        name_hash = hash_name(name, script_pubkey, register_addr=register_addr)

    script = 'NAME_PREORDER 0x%s 0x%s' % (name_hash, consensus_hash)
    hex_script = ysi_script_to_hex(script)
    packaged_script = add_magic_bytes(hex_script)
    
    return packaged_script


def make_outputs( data, inputs, sender_addr, burn_addr, fee, tx_fee, pay_fee=True, dust_included=False ):
    """
    Make outputs for a name preorder:
    [0] OP_RETURN with the name
    [1] address with the NAME_PREORDER sender's address
    [2] pay-to-address with the *burn address* with the fee
    Raise ValueError if there are not enough inputs to make the transaction
    """

    op_fee = max(fee, DEFAULT_DUST_FEE)
    total_tx_fee = tx_fee
    if not dust_included:
        total_tx_fee += (len(inputs) + 2) * DEFAULT_DUST_FEE + DEFAULT_OP_RETURN_FEE
    dust_value = DEFAULT_DUST_FEE

    bill = 0

    if pay_fee:
        bill = op_fee
    else:
        op_fee = 0
        bill = 0
        total_tx_fee = 0

    return [
        # main output
        {"script": virtualchain.make_data_script(str(data)),
         "value": 0},

        # change address (can be subsidy key)
        {"script": virtualchain.make_payment_script(str(sender_addr)),
         "value": virtualchain.calculate_change_amount(inputs, bill, total_tx_fee)},

        # burn address
        {"script": virtualchain.make_payment_script(str(burn_addr)),
         "value": op_fee}
    ]


def make_transaction(name, preorder_addr, register_addr, burn_addr, fee, consensus_hash,
                     blockchain_client, tx_fee=0, subsidize=False, safety=True,
                     dust_included=False):
    """
    Builds and broadcasts a preorder transaction.
    """

    preorder_addr = str(preorder_addr)
    register_addr = str(register_addr)
    name = str(name)
    consensus_hash = str(consensus_hash)
    fee = int(fee)
    tx_fee = int(tx_fee)

    assert is_name_valid(name)
    assert len(consensus_hash) == LENGTH_CONSENSUS_HASH * 2

    inputs = None
    private_key_obj = None
    script_pubkey = None    # to be mixed into preorder hash

    pay_fee = True
    if subsidize:
        pay_fee = False

    # tx only
    inputs = tx_get_unspents( preorder_addr, blockchain_client )
    if safety:
        assert len(inputs) > 0, "No UTXOs for {}".format(preorder_addr)

    script_pubkey = virtualchain.make_payment_script( preorder_addr )

    nulldata = build( name, script_pubkey, register_addr, consensus_hash)
    outputs = make_outputs(nulldata, inputs, preorder_addr, burn_addr, fee, tx_fee, pay_fee=pay_fee,
                           dust_included = dust_included)

    return (inputs, outputs)

def get_fees( inputs, outputs ):
    """
    Given a transaction's outputs, look up its fees:
    * the first output must be an OP_RETURN, and it must have a fee of 0.
    # the second must be the change address
    * the third must be a burn fee to the burn address.
    
    Return (dust fees, operation fees) on success 
    Return (None, None) on invalid output listing
    """
    if len(outputs) != 3:
        log.debug("Expected 3 outputs; got %s" % len(outputs))
        return (None, None)
    
    # 0: op_return
    if not virtualchain.tx_output_has_data( outputs[0] ):
        log.debug("outputs[0] is not an OP_RETURN")
        return (None, None) 
    
    if outputs[0]["value"] != 0:
        log.debug("outputs[0] has value %s'" % outputs[0]["value"])
        return (None, None) 
    
    # 1: change address 
    if virtualchain.script_hex_to_address( outputs[1]["script"] ) is None:
        log.error("outputs[1] has no decipherable change address")
        return (None, None)
    
    # 2: burn address 
    addr_hash = virtualchain.script_hex_to_address( outputs[2]["script"] )
    if addr_hash is None:
        log.error("outputs[2] has no decipherable burn address")
        return (None, None) 
    
    # should match make_outputs()
    # the +2 comes from 2 new outputs
    dust_fee = (len(inputs) + 2) * DEFAULT_DUST_FEE + DEFAULT_OP_RETURN_FEE
    op_fee = outputs[2]["value"]
    
    return (dust_fee, op_fee)



def snv_consensus_extras( name_rec, block_id, blockchain_name_data ):
    """
    Calculate any derived missing data that goes into the check() operation,
    given the block number, the name record at the block number, and the db.
    """
    return {}
