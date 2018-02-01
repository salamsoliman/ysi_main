# Blockstack snap

A [snap](https://snapcraft.io) package offers a secure and isolated environment
for applications, with automatic and transactional updates. The ysi snap
can be installed in all the
[supported Linux distros](https://snapcraft.io/docs/core/install).

## Install

To help testing the upcoming stable release, you can install the snap from the beta channel:

    $ sudo snap install ysi --beta
    
Or you can install the latest `ysi` and help testing the most recent changes with:

    $ sudo snap install ysi --edge

## Build

To build this snap from source in an Ubuntu 16.04 machine, or later:

    $ sudo apt install git snapcraft
    $ git clone https://github.com/ysi/ysi-core
    $ cd ysi-core/images/community
    $ snapcraft
    $ sudo snap install *.snap --dangerous

## Continuous delivery

We have a [Travis-CI job](https://github.com/elopio/ysi-core/blob/develop/.travis.yml) that runs daily to sync the maintainer branch with the latest upstream `develop` branch. If that job finds a new git tag in the repo that has not been released as a snap, it will patch the `snapcraft.yaml` file to build the snap corresponding to that tag. Otherwise, it will just leave it to build from the latest commit in `develop`.

Then, [launchpad](https://code.launchpad.net/~elopio/+snap/ysi) will build and release the snap to the `edge` channel.
