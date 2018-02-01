Demo: Blockstack-files
======================

CLI program for loading and storing files with Blockstack's RESTful API.

Sample usage, once completed:

```
$ pwd
python-filesharing
$ ls
README.md
bin
ysi_files
ysi_files.egg-info
build
dist
setup.py
$ ysi-files login PASSWORD
$ ysi-files ls /

$ ysi-files mkdir /foo
$ ysi-files ls /
foo/
$ ysi-files mkdir /bar
$ ysi-files ls /
bar/
foo/
$ ysi-files put ./setup.py /foo/setup.py
$ ysi-files ls /
bar/
foo/
$ ysi-files ls /foo
setup.py
$ ysi-files cat /foo/setup.py
#!/usr/bin/env python

from setuptools import setup, find_packages

# to set __version__
exec(open('ysi_files/version.py').read())

setup(
    name='ysi-files',
    version=__version__,
    url='https://github.com/ysi/ysi-core',
    license='GPLv3',
    author='Blockstack.org',
    author_email='support@ysi.org',
    description='Blockstack encrypted file sharing demo',
    keywords='blockchain git crypography name key value store data',
    packages=find_packages(),
    download_url='https://github.com/ysi/ysi-core/archive/master.zip',
    zip_safe=False,
    include_package_data=True,
    scripts=['bin/ysi-files'],
    install_requires=[
        'ysi>=0.14.1',
        'pyelliptic>=1.5.7',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

$ ysi-files rm /foo/setup.py
$ ysi-files ls /foo

$ ysi-files ls /
bar/
foo/
$ ysi-files rmdir /foo
$ ysi-files rmdir /bar
$ ysi-files ls /

$
```
