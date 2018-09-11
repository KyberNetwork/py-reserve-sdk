Operation Guide
===============

Initialize
----------
Create a :class:`Reserve <reserve_sdk.Reserve>` given the deployed 
reserve contract addresses, provider, account::

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

Each contract in reserve has these methods to control the permission:

* :meth:`Get current admin <reserve_sdk.BaseContract.admin>`
* :meth:`Transfer admin <reserve_sdk.BaseContract.transfer_admin>`
* :meth:`Pending admin <reserve_sdk.BaseContract.pending_admin>`
* :meth:`Claim admin <reserve_sdk.BaseContract.claim_admin>`
* :meth:`Add operator <reserve_sdk.BaseContract.add_operator>`
* :meth:`Get operators <reserve_sdk.BaseContract.operators>`
* :meth:`Add alerter <reserve_sdk.BaseContract.add_alerter>`
* :meth:`Get alerters <reserve_sdk.BaseContract.alerters>`

Transfer admin, add/remove operator, alerter with fund contract::

    >> fund = reserve.fund
    >> new_admin_addr = '0x...'
    >> fund.transfer_admin(new_admin_addr)
    >> assert new_admin_addr in fund.pending_admin()

    >> operator_addr = '0x...'
    >> fund.add_operator(operator_addr)
    >> assert operator_addr in fund.operators()

    >> alerter_addr = '0x...'
    >> fund.add_alerter(alerter_addr)
    >> assert alerter_addr in fund.alerters()

Funding
-------

Withdraw fund from reserve might happen frequently, to protect the fund,
a limited list of withdrawal addresses per token is defined. Only admin can 
alter the list through methods
:meth:`approve_withdraw_address \
<reserve_sdk.Reserve.approve_withdraw_address>`
or
:meth:`disapprove_withdraw_address \
<reserve_sdk.Reserve.disapprove_withdraw_address>`. The operator can only 
withdraw token to a whitelisted address by calling the method 
:meth:`withdraw \
<reserve_sdk.Reserve.withdraw>`.

Methods
+++++++

* :meth:`Get reserve balance <reserve_sdk.Reserve.get_balance>`
* :meth:`Approve withdraw address<reserve_sdk.Reserve.approve_withdraw_address>`
* :meth:`Disapprove withdraw address<reserve_sdk.Reserve.disapprove_withdraw_address>`
* :meth:`Check withdraw address<reserve_sdk.Reserve.approved_withdraw_address>`
* :meth:`Withdraw token<reserve_sdk.Reserve.withdraw>`

Examples
++++++++

.. code-block:: python

    reserve.get_balance('erc20_token_addr') # get reserve balance
    reserve.approve_withdraw_addresses(
        'dst_addr', 'erc20_token_addr') # require admin permission
    assert reserve.approved_withdraw_address(
        'dst_addr', 'erc20_token_addr')
    reserve.withdraw(
        'erc20_token_addr', token_unit, 'dst_addr'
    ) # require operator permission
    reserve.disapprove_withdraw_addresses(
        'dst_addr', 'erc20_token_addr') # require admin permission


Pricing
-------


.. note::
    In order to set rates, you should call
    :meth:`Reserve.add_new_token <reserve_sdk.Reserve.add_new_token>` to your 
    reserve first, then also remember to 
    :meth:`Reserve.set_valid_rate_duration_in_blocks
    <reserve_sdk.Reserve.set_valid_rate_duration_in_blocks>` to make your 
    rate valid.

To update the conversion rates, you have to call 
:meth:`Reserve.set_rate` with your tokens, the buy/sell rates in
seperately list. 

These flat rates might not be sufficient. A user with
a big buy/sell order will have different impact on your porfolio compared to 
other smaller orders. Therefore, the contract could use steps function to 
provide the price depend on the buy/sell amount, also the net traded amount 
between price update operations.

.. seealso::
    `Steps function <https://dev-developer.knstats.com/docs/ReservesGuide#step-functions>`_.

Methods:
++++++++

* :meth:`Add token <reserve_sdk.Reserve.add_new_token>`
* :meth:`Set rates <reserve_sdk.Reserve.set_rates>`
* :meth:`Set quantity step function <reserve_sdk.Reserve.set_qty_step_function>`
* :meth:`Set imbalance step function <reserve_sdk.Reserve.set_imbalance_step_function>`
* :meth:`Set valid rate duration in blocks<reserve_sdk.Reserve.set_valid_rate_duration_in_blocks>`
* :meth:`Get buy rate <reserve_sdk.Reserve.get_buy_rate>`
* :meth:`Get sell rate <reserve_sdk.Reserve.get_sell_rate>`

Examples
++++++++

List new token to your reserve::

    >> reserve.add_new_token(
        token='0xdd974D5C2e2928deA5F71b9825b8b646686BD200',  # ERC20: KNC
        minimal_record_resolution=0.0001 * 10**18, # token unit equivalent of $0.0001
        max_per_block_imbalance=439.79 * 10**18, # the maximum of change for a token in a block
        max_total_imbalance=922.36 * 10**18 # the maximum of change for a token between 2 prices update
    )

Set rates::

    >> reserve.set_rates(
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

    >> reserve.set_qty_step_function(
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

    >> reserve.set_imbalance_step_function(
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

Get rates::

    >> reserve.get_buy_rate('token-address', quantity)
    500000000000000000000
    >> reserve.get_sell_rate('token-address', quantity)
    1820000000000000

Sanity
------

To provide a safeguard for reserves, you can set the sanity rates to disabled
trades in case conversion rates fall below a lower limit or rise above a 
upper limit.

.. seealso::
    `Sanity rates <https://developer.kyber.network/docs/MiscellaneousGuide#sanity-rates>`_.

Methods:
++++++++

* :meth:`Set sanity rates<reserve_sdk.Reserve.set_sanity_rates>`
* :meth:`Get sanity rates<reserve_sdk.Reserve.get_sanity_rates>`
* :meth:`Set reasonable diff<reserve_sdk.Reserve.set_reasonable_diff>`
* :meth:`Get reasonable diff<reserve_sdk.Reserve.get_reasonable_diff_in_bps>`

Examples
++++++++

Set/Get sanity rates::

    >> reserve.set_sanity_rates(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [0.002 * 10**18] # uint[] 1 KNC = 0.002 ETH = 2000000000000000 wei
    )

    >> rate = reserve.get_sanity_rates(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200', # KNC
        '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' # ETH
    )

Set/Get reasonable difference in basis points::

    >> reserve.set_reasonable_diff(
        ['0xdd974D5C2e2928deA5F71b9825b8b646686BD200'], # ERC20[]: [KNC token]
        [1000] # uint[]: 10% = 1000 bps
    )

    >> diff = reserve.get_reasonable_diff_in_bps(
        '0xdd974D5C2e2928deA5F71b9825b8b646686BD200' # ERC20: KNC address
    )