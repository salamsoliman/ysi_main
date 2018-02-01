# Blockstack Core on AWS

We're releasing a listing on the AWS Marketplace, where you can easily deploy
the latest version of Blockstack core (with fastsync support).

- **Step 1:** Login to your AWS account or create one if you don't already have one.

- **Step 2:** Deploy a new VM from the Blockstack image, with at least 20 GB of space on the root volume.

- **Step 3:** Login to your newly deployed node.

- **Step 4:** Use fastsync to get the latest state:

```
$ ysi-server --debug fast_sync http://fastsync.ysi.org/snapshots/latest.bsk 023fa2e30724998010764529bda23213061c8e758d7095e1883bed8006844daaec
```

- **Step 5:** Start the Blockstack Core node:

```
$ ysi-server --debug start
$ tail -f ~/.ysi-server/ysi-server.log
```

If you run into any issues, you can talk to us in the #support channel at http://chat.ysi.org

Note: fastsyn command usage is changing and we'll update it shortly:
```
$ ysi-core --debug fast_sync http://40.121.156.215/snapshot.bsk
```