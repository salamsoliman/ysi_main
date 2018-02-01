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

class BlockchainClient(object):
    """ Type parameter can be 'bitcoind', 'blockchain.info', 'chain.com',
        'blockcypher.com', etc.
        Auth object is a two item tuple.
    """

    def __init__(self, type, auth=None, timeout=None):
        self.type = type

        if isinstance(auth, tuple) and len(auth) == 2:
            self.auth = auth
        else:
            raise Exception('auth must be a two-item tuple')
