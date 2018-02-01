#!/usr/bin/env python2

from setuptools import setup, find_packages

# to set __version__
exec(open('ysi_integration_tests/version.py').read())

print 'version = {}'.format(__version__)

setup(
    name='ysi-integration-tests',
    version=__version__,
    url='https://github.com/ysi/ysi-integration-tests',
    license='GPLv3',
    author='Blockstack.org',
    author_email='support@ysi.org',
    description='Integration tests for Blockstack packages',
    keywords='blockchain bitcoin btc cryptocurrency name key value store data',
    packages=find_packages(),
    scripts=[
        'bin/ysi-test-scenario',
        'bin/ysi-test-check-serialization',
        'bin/ysi-test-all',
        'bin/ysi-test-all-junit',
        'bin/ysi-test-env',
        'bin/ysi-netlog-server',
    ],
    download_url='https://github.com/ysi/ysi-integration-tests/archive/master.zip',
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'ysi>=0.17.0',
        'xmlrunner>=1.7.7',
        'influxdb>=4.1.1'
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
