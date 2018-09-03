.. reserve_sdk documentation master file, created by
   sphinx-quickstart on Mon Sep  3 00:28:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to reserve_sdk's documentation!
=======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Reserve
-------

Contracts
+++++++++

* Reserve contract (Funding)
* Conversion rates contract (Pricing)
* Sanity rates contract (Sanity)

Role
++++

Each contract in reserve has three permission groups:

1. Admin.
2. Operator.
3. Alerter.

Deploy
------

Deploy reserve contract given the provider, account. The returned addresses
contains reserve contract, pricing contract and sanity contract address::

    >> from web3 import Web3, HTTPProvider
    >> from reserve_sdk import Deployer

    >> provider = HTTPProvider('https://ropsten.infura.io')
    >> w3 = Web3(provider)
    >> account = w3.eth.account.privateKeyToAccount('private-key')

    >> d = Deployer(provider, account)
    >> addresses = d.deploy('kyber-network-address')

Operation
---------

Initialize
++++++++++
Create a reserve instance given the deployed reserve contract addresses,
provider, account::

    >> from web3 import Web3, HTTPProvider
    >> from reserve_sdk import Addresses, Reserve

    >> provider = HTTPProvider('https://ropsten.infura.io')
    >> w3 = Web3(provider)
    >> account = w3.eth.account.privateKeyToAccount('private-key')

    >> addresses = Addresses(reserve_addr, pricing_addr, sanity_addr)
    >> reserve = Reserve(provider, account, addresses)

Permission
++++++++++

Transfer admin, add/remove operator, alerter::

    >> new_admin_addr = '0x...'
    >> reserve.reserve_contract.transfer_admin(new_admin_addr)
    >> assert new_admin_addr in reserve.reserve_contract.pending_admin()

    >> operator_addr = '0x...'
    >> reserve.reserve_contract.add_operator(operator_addr)
    >> assert operator_addr in reserve.reserve_contract.operators()

    >> alerter_addr = '0x...'
    >> reserve.reserve_contract.add_alerter(alerter_addr)
    >> assert alerter_addr in reserve.reserve_contract.alerters()

Funding
+++++++

Check reserve balance::

    >> reserve.reserve_contract.get_balance('erc20_token_addr')

Approve/Disapprove to withdraw token from reserve to an address::

    >> reserve.reserve_contract.approve_withdraw_addresses(
        'dst_addr', 'erc20_token_addr')
    
    >> reserve.reserve_contract.disapprove_withdraw_addresses(
        'dst_addr', 'erc20_token_addr')

Checking if an address can receive token from reserve::

    >> assert reserve.reserve_contract.approved_withdraw_address(
        'dst_addr', 'erc20_token_addr')

Withdraw token from reserve, this action should be execute by operator::

    >> reserve.reserve_contract.withdraw(
        'erc20_token_addr', token_unit, 'dst_addr')

Pricing
+++++++

List new token to your reserve::

    >> reserve.conversion_rates_contract.add_new_token(
        token='0xdd974D5C2e2928deA5F71b9825b8b646686BD200',  # ERC20: KNC
        minimal_record_resolution=0.0001 * 10**18, # token unit equivalent of $0.0001
        max_per_block_imbalance=439.79 * 10**18, # the maximum of change for a token in a block
        max_total_imbalance=922.36 * 10**18 # the maximum of change for a token between 2 prices update
    )

Set rates::

    >> reserve.conversion_rates_contract.set_rates(
        token_addresses=[
            '0xdd974D5C2e2928deA5F71b9825b8b646686BD200', # KNC
            '0xd26114cd6EE289AccF82350c8d8487fedB8A0C07'  # OMG
        ],
        buy_rates=[
            500 * 10**18,
            600 * 10**18
        ],
        sell_rates=[
            0.00182 * 10**18,
            0.00192 * 10**18
        ]
    )

Set quantity step function::

    >> reserve.conversion_rates_contract.set_qty_step_function(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'],  # ERC20[]
        [
            100 * 10**18,
            200 * 10**18,
            300 * 10**18,
            500 * 10**18
        ],  # x_buy
        [
            0,
            -30,
            -60,
            -80
        ],  # y_buy
        [
            100 * 10**18,
            200 * 10**18,
            300 * 10**18,
            500 * 10**18
        ], # x_sell
        [
            0,
            -30,
            -60,
            -80
        ]  # y_sell
    )

Set imbalance step function::

    >> reserve.conversion_rates_contract.set_imbalance_step_function(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'],  # ERC20[]
        [
            100 * 10**18,
            200 * 10**18,
            300 * 10**18,
            500 * 10**18
        ], # x_buy
        [
            0,
            -30,
            -60,
            -80
        ], # y_buy
        [
            300 * 10**18,
            200 * 10**18,
            100 * 10**18,
            0
        ], # x_sell
        [
            -70,
            -50,
            -25,
            0
        ] # y_sell
    )

Sanity
++++++

Set/Get sanity rates::

    >> reserve.sanity_rate_contract.set_sanity_rates(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [0.002 * 10**18] # uint[] 1 KNC = 0.002 ETH = 2000000000000000 wei
    )

    >> rate = reserve.get_sanity_rates(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200', # KNC
        '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' # ETH
    )

Set/Get reasonable difference in basis points::

    >> reserve.sanity_rate_contract.set_reasonable_diff(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [1000] # uint[]: 10% = 1000 bps
    )

    >> diff = reserve.get_reasonable_diff_in_bps(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200' # ERC20: KNC address
    )