Operation Guide
===============

Initialize
----------
Create a reserve instance given the deployed reserve contract addresses,
provider, account::

    >> from web3 import Web3, HTTPProvider
    >> from reserve_sdk import Addresses, Reserve

    >> provider = HTTPProvider('https://ropsten.infura.io')
    >> w3 = Web3(provider)
    >> account = w3.eth.account.privateKeyToAccount('private-key')

    >> reserve_contract_addr = '0x...'
    >> conversion_rates_contract_addr = '0x...'
    >> sanity_rates_contract_addr = '0x...'
    >> addresses = Addresses(
        reserve_contract_addr, 
        conversion_rates_contract_addr, 
        sanity_rates_contract_addr
    )
    >> reserve = Reserve(provider, account, addresses)

Permission
----------

Transfer admin, add/remove operator, alerter::

    >> new_admin_addr = '0x...'
    >> reserve.fund.transfer_admin(new_admin_addr)
    >> assert new_admin_addr in reserve.fund.pending_admin()

    >> operator_addr = '0x...'
    >> reserve.fund.add_operator(operator_addr)
    >> assert operator_addr in reserve.fund.operators()

    >> alerter_addr = '0x...'
    >> reserve.fund.add_alerter(alerter_addr)
    >> assert alerter_addr in reserve.fund.alerters()

Funding
-------

Check reserve balance::

    >> reserve.fund.get_balance('erc20_token_addr')

Approve/Disapprove to withdraw token from reserve to an address::

    >> reserve.fund.approve_withdraw_addresses(
        'dst_addr', 'erc20_token_addr')
    
    >> reserve.fund.disapprove_withdraw_addresses(
        'dst_addr', 'erc20_token_addr')

Checking if an address can receive token from reserve::

    >> assert reserve.fund.approved_withdraw_address(
        'dst_addr', 'erc20_token_addr')

Withdraw token from reserve, this action should be execute by operator::

    >> reserve.fund.withdraw(
        'erc20_token_addr', token_unit, 'dst_addr'
    )

Pricing
-------

List new token to your reserve::

    >> reserve.pricing.add_new_token(
        token='0xdd974D5C2e2928deA5F71b9825b8b646686BD200',  # ERC20: KNC
        minimal_record_resolution=0.0001 * 10**18, # token unit equivalent of $0.0001
        max_per_block_imbalance=439.79 * 10**18, # the maximum of change for a token in a block
        max_total_imbalance=922.36 * 10**18 # the maximum of change for a token between 2 prices update
    )

Set rates::

    >> reserve.pricing.set_rates(
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

    >> reserve.pricing.set_qty_step_function(
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

    >> reserve.pricing.set_imbalance_step_function(
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
------

Set/Get sanity rates::

    >> reserve.sanity.set_sanity_rates(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [0.002 * 10**18] # uint[] 1 KNC = 0.002 ETH = 2000000000000000 wei
    )

    >> rate = reserve.get_sanity_rates(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200', # KNC
        '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' # ETH
    )

Set/Get reasonable difference in basis points::

    >> reserve.sanity.set_reasonable_diff(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [1000] # uint[]: 10% = 1000 bps
    )

    >> diff = reserve.get_reasonable_diff_in_bps(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200' # ERC20: KNC address
    )