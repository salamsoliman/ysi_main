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
        'ysi>=0.14.2',
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
