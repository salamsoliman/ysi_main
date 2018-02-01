# Blockstack Integration Tests

This is the end-to-end Blockstack test framework. New Blockstack
developers should familiarize themselves with this first, since the
integration tests offer a straightforward way to set up and run all
the components in a sandboxed environment.

Once installed, developers can easily interact with a fully-featured
Blockstack core node running on a private Bitcoin blockchain.

# Getting Started with Docker

The easiest way to get started with our integration tests is to use
our integration test docker images.

You can pull the integration test image from quay.

```bash
docker pull quay.io/ysi/integrationtests:develop
```

To see a full list of tags check out our [Quay repo](https://quay.io/organization/ysi)!

The `test-launcher` tool can also be used to build an integration test
image from your local repository.

Once you have the docker image, you can run individual test
scenarios. Test scenarios are organized as Python modules, which can
be imported from `ysi_integration_tests.scenarios`. For
example, the following command runs the test that will create a
`.id` namespace, preorder and register the name `foo.id`, set its
zonefile hash, and create an empty profile for it:

```bash
IMAGE=$(docker run -dt -v /tmp:/tmp quay.io/ysi/integrationtests:develop ysi-test-scenario ysi_integration_tests.scenarios.portal_test_env)
```

You can check the status of the test:

```bash
docker logs -f $IMAGE
```

And stop the test with:
```bash
docker stop $IMAGE
```

## Running interactive tests with Docker

You can setup an interactive regtest environment for connecting to a
Blockstack Browser (or interaction via the CLI).

In interactive mode, a test idles after its checks finish (i.e. after
`check()` returns).  This leaves you with a running Bitcoin node and a
running Blockstack Core node that you can interact with via the
Blockstack CLI, as if it were a production system.

To start a test in interactive mode, pass the `--interactive` switch.

For example, with the docker file already pulled, you can execute:

```bash
IMAGE=$(docker run -dt -p 6270:6270 -v /tmp:/tmp -e BLOCKSTACK_TEST_CLIENT_RPC_PORT=6270 -e BLOCKSTACK_TEST_CLIENT_BIND=0.0.0.0 quay.io/ysi/integrationtests:develop ysi-test-scenario --interactive 2 ysi_integration_tests.scenarios.portal_test_env)
```

You know the setup has finished when it has displayed in the log:

```bash
$ docker logs -f $IMAGE | grep inished
```

The API password for connecting from the browser is:

```
ysi_integration_test_api_password
```

Note: To obtain regtest bitcoins in the browser's wallet during testing-mode,
use the hidden browser page (http://localhost:8888/wallet/send-core) or
(http://localhost:3000/wallet/send-core) to send bitcoins to the address.

## Using CLI commands from the docker container

To use the CLI commands once your docker container has started, connect to the docker container:

```bash
docker exec -it $IMAGE bash
```

And from the container, set the test environment variables:

```bash
     $ export BLOCKSTACK_TEST=1    # tells Blockstack CLI that it's running with the test environment
     $ export BLOCKSTACK_TESTNET=1 # tells Blockstack CLI to use testnet addresses
     $ export BLOCKSTACK_DEBUG=1   # print debug-level output in the CLI; great for troubleshooting
     $ export BLOCKSTACK_CLIENT_CONFIG=/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.portal_test_env/client/client.ini
```

You can also set these variables with an automated script included in the test
framework:

```bash
    $ . $(which ysi-test-env) portal_env_test
    |ysi-test portal_env_test| $
```

Your `$PS1` variable will be updated to show the name of the test if you take
this option.  You can unset the environment variables with `. $(which
ysi-test-env) deactivate`.

With these variables set, you can now run `ysi` commands from the container shell:

```bash
     $ ysi lookup foo.id
```

# Getting Started with Python virtualenv and local bitcoind

You can run the integration test framework without using our docker containers, however, this
requires a bit more setup.


To install the test framework, first install `ysi-core` and all of its
dependencies (done above).

```bash
    $ virtualenv --python=python2 ysi-testing
    $ cd ysi-testing
    $ source bin/activate
    (ysi-testing) $ git clone https://github.com/ysi/ysi-core ysi-core
    (ysi-testing) $ cd ysi-core/ && ./setup.py build && ./setup.py install
```

**macOS Note**: Installing the python `scrypt` library on macOS
requires OpenSSL headers. Those can be obtained via HomeBrew (and
setup using environment variables `LDFLAGS` and
`CPPFLAGS`). Alternatively, you can use the virtualenv tarball that
ships with our macOS releases of Blockstack Browser. Generally, on
macOS, it is much easier to setup our test environment with Docker.

Then, do the following to install the integration tests:

```
    $ cd integration_tests/
    $ ./setup.py build && sudo ./setup.py install
```

## Installing bitcoind in macOS

You'll need the `bitcoind` console app, which apparently doesn't
come included with `Bitcoin-QT` on macOS, so we'll need to build
it from source, using this [guide](https://github.com/bitcoin/bitcoin/blob/master/doc/build-osx.md)

Summary:
```bash
$ brew install automake berkeley-db4 libtool boost --c++11 miniupnpc openssl pkg-config protobuf qt libevent
$ git clone https://github.com/bitcoin/bitcoin
$ cd bitcoin
$ ./autogen.sh
$ ./configure
$ make
```

You need to add the `src/` directory from your bitcoind build to your
path:

```
$ export PATH=/Users/Whomever/Wherever/bitcoin/src:$PATH
```


## Running tests

Run a test with the `ysi-test-scenario` command

```
     $ ysi-test-scenario ysi_integration_tests.scenarios.rpc_register
```

If all is well, the test will run for a 5-10 minutes and print:

```
     SUCCESS ysi_integration_tests.scenarios.rpc_register
```

## Interactive Testing

This example will set up an interactive regtest node that you can connect to via Blockstack Browser

```bash
 $ BLOCKSTACK_TEST_CLIENT_RPC_PORT=6270 ysi-test-scenario --interactive 2 ysi_integration_tests.scenarios.portal_test_env
```

### Using the CLI

To interact with this using the Blockstack Browser, you need to use the api_password:

```
ysi_integration_test_api_password
```

Note: To obtain regtest bitcoins in the browser's wallet during testing-mode,
use the hidden browser page [http://localhost:8888/wallet/send-core] or
[http://localhost:3000/wallet/send-core] to send bitcoins to the address.

### Using the CLI

While the test is idling, you can interact with the Blockstack Core node with the Blockstack CLI.  To do so, you'll need to set
the following environment variables:

```
     $ export BLOCKSTACK_TEST=1    # tells Blockstack CLI that it's running with the test environment
     $ export BLOCKSTACK_TESTNET=1 # tells Blockstack CLI to use testnet addresses
     $ export BLOCKSTACK_DEBUG=1   # print debug-level output in the CLI; great for troubleshooting
     $
     $ # this tells the CLI where to find the test-generated config file
     $ export BLOCKSTACK_CLIENT_CONFIG=/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.rpc_register/client/client.ini
```

Once set, you can use the Blockstack CLI as normal, and it will interact with the test case's Blockstack Core node:

```
     $ ysi lookup foo.test
     {
         "profile": {
             "@type": "Person",
             "accounts": []
         },
         "zonefile": '$ORIGIN foo.test\n$TTL 3600\npubkey TXT "pubkey:data:03762f2da226d9c531e8ed371c9e133bfbf42d8475778b7a2be92ab0b376539ae7"\n_file URI 10 1 "file:///tmp/ysi-disk/mutable/foo.test"'
     }
```

# Information on the testing Framework

Internally, the test-runner (`ysi-test-scenario`) starts up a
Bitcoin node locally in `-regtest` mode, giving the test its own
private testnet blockchain.  It mines some blocks with Bitcoin, fills
some test-specified addresses with an initial balance (those specified
in the test module's `wallets` global variable), and sets up a
temporary configuration directory tree in
`/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.<foo>/`.

Once Bitcoin is ready, the test-runner starts up Blockstack Core and
has it crawl the local Bitcoin blockchain.  It then runs the test's
`scenario()` method, which feeds it a string of Blockstack CLI
commands at the desired block heights.  Once the `scenario()` method
finishes, the test runner calls the `check()` method to verify that
the test generated the right state.  If this passes, the test-runner
verifies the Blockstack node's database integrity, performs automated
SNV tests, and checks that the Atlas network crawled the right
zonefiles.


Relevant Files, Ports, Tips, and Tricks
---------------------------------------

* Bitcoin in regtest mode runs its JSON-RPC server on port 18332, and its peer-to-peer endpoint on port 18444.

* The Blockstack Core indexer and Atlas peer runs on port 16264.  **This is a private API; do not talk to it directly.**

* The Blockstack RESTful HTTP endpoint (implemented by the API daemon) runs on port 16268.  **This is what you want to use to programmatically interact with Blockstack.**

* All state for a given test is located under `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/`, where `${SCENARIO_NAME}` is the name of the test (e.g. `rpc_register`).

* The CLI's config file (also the API daemon's config file) is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/client/client.ini`.

* The API daemon's log file is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/client/api_endpoint.log`.

* The API daemon's PID file is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/client/api_endpoint.pid`.

* The API daemon's wallet file is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/client/wallet.json`.

* The Atlas and indexer node's config file is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/ysi-server.ini`.

* The Sqlite3 name database is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/ysi-server.db`.

* The consensus hash history for the Core node is located at `/tmp/ysi-run-scenario.ysi_integration_tests.scenarios.${SCENARIO_NAME}/ysi-server.snapshots`.

Troubleshooting
---------------

* We use `rpc_register` as a sample test here, because if it works, then it
  means that everything is working.  If `rpc_register` fails, try
  `name_preorder_register` instead (it does NOT start the API daemon; it only
  tests ysi's name registration on-chain).  If that fails, then there's
  probably something wrong with your installation.

* Before starting your test, make sure that there are no `bitcoind -regtest`
  processses running.  Also, make sure that there are no lingering integration
  tests processes running.  This can happen if your test encounters a fatal
  error and does not get a chance to clean itself up properly.

* One common error is that the API daemon may fail to start.  You can start it explicitly with `ysi api start`, and stop it with `ysi api stop`.
  If for some reason you need to (re)start the API daemon, the default wallet password is `0123456789abcdef`.

* If your API endpoint fails to start, you should check the `api_endpoint.log` file in order to verify that the API daemon didn't crash or misbehave.

* You can verify that your API endpoint is running with `curl http://localhost:16268`.  You should get back a simple HTML page.

* Test output can be lengthy.  If you want to preserve it, we recommend `tee(1)`-ing it to a log file.

CLI Examples
--------

You can register names like normal when running the test in interactive mode:

```
     $ ysi register bar.test
     Registering bar.test will cost 0.06481015 BTC.
     The entire process takes 30 confirmations, or about 5 hours.
     You need to have Internet access during this time period, so
     this program can send the right transactions at the right
     times.

     Continue? (Y/n): y
     {
         "message": "The name has been queued up for registration and will take a few hours to go through. You can check on the status at any time by running 'ysi info'.", 
         "success": true,
         "transaction_hash": "4fa9cd94f195b1aa391727c8949d88dbae25eddf1097bc8930fdb44c6a27b3d7"
     }
```

You can check the status of the name as it gets registered on the regtest blockchain, just as you would on the mainnet blockchain.
Because blocktimes are only 10 seconds in this example, names get registered quickly.

```
     $ ysi info             
     {
         "advanced_mode": true, 
         "cli_version": "0.14.2", 
         "consensus_hash": "bf168a3b5437c11c744891d38dffb8f2", 
         "last_block_processed": 305, 
         "last_block_seen": 305, 
         "queue": {
             "preorder": [
                 {
                     "confirmations": 7, 
                     "name": "bar.test", 
                     "tx_hash": "4fa9cd94f195b1aa391727c8949d88dbae25eddf1097bc8930fdb44c6a27b3d7"
                 }
             ]
         }, 
         "server_alive": true, 
         "server_host": "localhost", 
         "server_port": 16264, 
         "server_version": "0.14.2"
     }
```

As far as Blockstack is concerned, it thinks its running on the Bitcoin testnet.  As such, you'll see that your names are
owned by testnet-formatted addresses:

```
     $ ysi names
     {
         "addresses": [
             {
                 "address": "n44rMyQ9rhTf7KjFdRwDNMWUSJ3MWLsDQ4", 
                 "names_owned": [
                     "foo.test", 
                     "bar.test"
                 ]
             }
         ], 
         "names_owned": [
             "foo.test", 
             "bar.test"
         ]
     }
```
     
Once the name registers, you'll see that its profile and zonefile are automatically generated and stored,
and will be loaded from the pre-configured `disk` driver (the defualt driver used by the test framework):

```
    $ BLOCKSTACK_DEBUG=1 ysi lookup bar.test
    [2016-10-03 17:41:00,892] [DEBUG] [spv:110] (15317.139910730368768) Using testnet/regtest
    [2016-10-03 17:41:01,038] [WARNING] [config:104] (15317.139910730368768) TX_MIN_CONFIRMATIONS = 0
    [2016-10-03 17:41:01,038] [WARNING] [config:276] (15317.139910730368768) CONFIG_PATH = /tmp/ysi-run-scenario.ysi_integration_tests.scenarios.rpc_register/client/client.ini
    [2016-10-03 17:41:01,085] [DEBUG] [cli:210] (15317.139910730368768) Enabling advanced methods
    [2016-10-03 17:41:01,125] [DEBUG] [client:134] (15317.139910730368768) Loaded storage driver 'disk'
    [2016-10-03 17:41:01,140] [DEBUG] [storage:285] (15317.139910730368768) get_immutable b4d1edb5ea706310b4599540a8d76ead4c7afd96
    [2016-10-03 17:41:01,141] [DEBUG] [storage:311] (15317.139910730368768) Try disk (b4d1edb5ea706310b4599540a8d76ead4c7afd96)
    [2016-10-03 17:41:01,141] [DEBUG] [storage:345] (15317.139910730368768) loaded b4d1edb5ea706310b4599540a8d76ead4c7afd96 with disk
    [2016-10-03 17:41:01,206] [DEBUG] [storage:422] (15317.139910730368768) get_mutable bar.test
    [2016-10-03 17:41:01,206] [DEBUG] [storage:462] (15317.139910730368768) Try disk (file:///tmp/ysi-disk/mutable/bar.test)
    [2016-10-03 17:41:01,268] [DEBUG] [storage:492] (15317.139910730368768) loaded 'file:///tmp/ysi-disk/mutable/bar.test' with disk
    {
        "profile": {
            "@type": "Person", 
            "accounts": []
        }, 
        "zonefile": '$ORIGIN bar.test\n$TTL 3600\npubkey TXT "pubkey:data:039408bc142ffe926a5865cb35447bb6142c9170e74ec194186f96129a37eb9033"\n_file URI 10 1 "file:///tmp/ysi-disk/mutable/bar.test"\n'
    }
```

Namespace Creation Example
--------------------------

You can test out the namespace creation functions once you've got a shell
set up to connect to your regtest environment:

First, get the private keys you'll use for the namespace:
```bash
$ ysi wallet
{
    "data_privkey": "bb68eda988e768132bc6c7ca73a87fb9b0918e9a38d3618b74099be25f7cab7d01",
    "data_pubkey": "04ea5d8c2a3ba84eb17625162320bb53440557c71f7977a57d61405e86be7bdcdab63a7f1eda1e6c1670c64a9f532b9f55458019d9b80fdf41748d06cd7f60d451", 
    "owner_address": "myaPViveUWiiZQQTb51KXCDde4iLC3Rf3K",
    "owner_privkey": "8f87d1ea26d03259371675ea3bd31231b67c5df0012c205c154764a124f5b8fe01",
    "payment_address": "mvF2KY1UbdopoomiB371epM99GTnzjSUfj",
    "payment_privkey": "f4c3907cb5769c28ff603c145db7fc39d7d26f69f726f8a7f995a40d3897bb5201"
}
```

For testing, I use the `payment_privkey` above to fund the namespace creation and `owner_privkey`
as the namespace reveal key.

```bash
$ PAYMENTKEY="f4c3907cb5769c28ff603c145db7fc39d7d26f69f726f8a7f995a40d3897bb5201"
$ REVEALKEY="8f87d1ea26d03259371675ea3bd31231b67c5df0012c205c154764a124f5b8fe01"
```

Now, you can perform the preorder.
```bash
$ ysi namespace_preorder blankstein $PAYMENTKEY $REVEALKEY
```

Wait for the transaction to confirm, and then issue a "reveal". During
the reveal you configure the price function, expiration time of names,
and whether or not you receive funds.
```bash
$ ysi namespace_reveal blankstein $PAYMENTKEY $REVEALKEY
```

Once your reveal your namespace, you can issue a "ready", and then

```bash
$ ysi namespace_ready blankstein $REVEALKEY
```
