Deployment Guide
================

Deploy reserve contract given the provider, account. The returned 
:class:`Addresses <reserve_sdk.Addresses>`
contains reserve contract, pricing contract and sanity contract address::

    >> from web3 import Web3, HTTPProvider
    >> from reserve_sdk import Deployer

    >> provider = HTTPProvider('https://ropsten.infura.io')
    >> w3 = Web3(provider)
    >> account = w3.eth.account.privateKeyToAccount('private-key')

    >> d = Deployer(provider, account)
    >> addresses = d.deploy('kyber-network-address')
    Addresses(reserve='0x...', conversion_rates='0x...', sanity_rates='0x...')