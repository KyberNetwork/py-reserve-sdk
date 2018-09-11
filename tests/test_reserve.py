import unittest
from functools import wraps
import random

from web3 import Web3

from reserve_sdk import Reserve, Deployer
from reserve_sdk.utils import token_wei
from .utils import provider, test_accounts, tokens, NETWORK_ADDR

random.seed(0)

admin, admin_1, admin_2, operator, alerter = test_accounts[:5]
deployer = Deployer(provider, admin)
addresses = deployer.deploy(NETWORK_ADDR)
reserve = Reserve(provider, admin, addresses)


def role(account):
    """ Set specific account to execute contract function.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kargs):
            self.reserve.change_account(account)
            return func(self, *args, **kargs)

        return wrapper
    return decorator


class TestReserve(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reserve.fund.add_operator(operator.address)
        reserve.fund.add_alerter(alerter.address)
        reserve.pricing.add_operator(operator.address)
        reserve.pricing.add_alerter(alerter.address)
        reserve.sanity.add_operator(operator.address)
        reserve.sanity.add_alerter(alerter.address)

        reserve.set_valid_rate_duration_in_blocks(60)

        for token in tokens:
            token.transfer(addresses.reserve, token_wei(5000, 18))
            reserve.add_new_token(
                token=token.address,
                minimal_record_resolution=token_wei(0.0001, 18),
                max_per_block_imbalance=token_wei(439.79, 18),
                max_total_imbalance=token_wei(922.36, 18)
            )

    def setUp(self):
        self.reserve = reserve

    @role(admin)
    def test_link_contracts(self):
        self.reserve.link_contracts(
            NETWORK_ADDR,
            addresses.reserve,
            addresses.conversion_rates,
            addresses.sanity_rates
        )
        self.assertEqual(
            self.reserve.pricing.get_reserve_address(),
            addresses.reserve
        )
        self.assertEqual(
            self.reserve.fund.get_network_address(),
            NETWORK_ADDR
        )
        self.assertEqual(
            self.reserve.fund.get_conversion_rates_address(),
            addresses.conversion_rates
        )
        self.assertEqual(
            self.reserve.fund.get_sanity_rates_address(),
            addresses.sanity_rates
        )

    def test_get_balance(self):
        self.assertIsInstance(
            self.reserve.get_balance(tokens[0].address),
            int
        )

    def test_approve_disapprove_withdraw_address(self):
        self.assertFalse(
            self.reserve.approved_withdraw_address(
                operator.address, tokens[0].address
            )
        )

        self.reserve.approve_withdraw_address(
            operator.address, tokens[0].address
        )

        self.assertTrue(
            self.reserve.approved_withdraw_address(
                operator.address, tokens[0].address
            )
        )

        self.reserve.disapprove_withdraw_address(
            operator.address, tokens[0].address
        )

        self.assertFalse(
            self.reserve.approved_withdraw_address(
                operator.address, tokens[0].address
            )
        )

    def test_withdraw_by_operator(self):
        token = tokens[0]
        balance = self.reserve.get_balance(token.address)

        self.reserve.change_account(admin)
        self.reserve.approve_withdraw_address(operator.address, token.address)

        self.reserve.change_account(operator)
        self.reserve.withdraw(token.address, 10, operator.address)
        self.assertEqual(
            self.reserve.get_balance(token.address),
            balance - 10
        )
        self.reserve.change_account(admin)

    def test_enable_disable_trading_function(self):
        self.reserve.change_account(alerter)
        self.reserve.disable_trade()
        self.assertFalse(self.reserve.trade_enabled())

        self.reserve.change_account(admin)
        self.reserve.enable_trade()
        self.assertTrue(self.reserve.trade_enabled())

    @role(operator)
    def test_set_get_rates(self):
        token_addresses = [token.address for token in tokens]
        buy_rates = [token_wei(random.random() * 1000, 18) for _ in tokens]
        sell_rates = [token_wei(random.random(), 18) for _ in tokens]

        self.reserve.set_rates(token_addresses, buy_rates, sell_rates)

        for idx, token in enumerate(tokens):
            self.reserve.set_qty_step_function(
                token.address, [0], [0], [0], [0]
            )
            self.reserve.set_imbalance_step_function(
                token.address, [0], [0], [0], [0]
            )

            self.assertEqual(
                self.reserve.get_buy_rate(token.address, qty=1),
                buy_rates[idx]
            )

            self.assertEqual(
                self.reserve.get_sell_rate(token.address, qty=1),
                sell_rates[idx]
            )

    @role(operator)
    def test_quantity_step_functions(self):
        token = tokens[0]
        x_buy = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_buy = [0, -30, -60, -80]
        x_sell = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_sell = [0, -30, -60, -80]
        self.reserve.set_qty_step_function(
            token.address,
            x_buy,
            y_buy,
            x_sell,
            y_sell,
        )

        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 0, 0),
            len(x_buy)
        )
        for idx, step in enumerate(x_buy):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 1, idx),
                step
            )
        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 2, 0),
            len(y_buy)
        )
        for idx, impact in enumerate(y_buy):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 3, idx),
                impact
            )

        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 4, 0),
            len(x_sell)
        )
        for idx, step in enumerate(x_sell):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 5, idx),
                step
            )
        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 6, 0),
            len(y_sell)
        )
        for idx, impact in enumerate(y_sell):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 7, idx),
                impact
            )

    @role(operator)
    def test_imbalance_step_function(self):
        token = tokens[0]
        x_buy = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_buy = [0, -30, -60, -80]
        x_sell = [300 * 10**18, 200 * 10**18, 100 * 10**18, 0]
        y_sell = [-70, -50, -25, 0]
        self.reserve.set_imbalance_step_function(
            token.address,
            x_buy,
            y_buy,
            x_sell,
            y_sell,
        )

        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 8, 0),
            len(x_buy)
        )
        for idx, step in enumerate(x_buy):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 9, idx),
                step
            )
        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 10, 0),
            len(y_buy)
        )
        for idx, impact in enumerate(y_buy):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 11, idx),
                impact
            )

        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 12, 0),
            len(x_sell)
        )
        for idx, step in enumerate(x_sell):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 13, idx),
                step
            )
        self.assertEqual(
            self.reserve.get_steps_function_data(token.address, 14, 0),
            len(y_sell)
        )
        for idx, impact in enumerate(y_sell):
            self.assertEqual(
                self.reserve.get_steps_function_data(token.address, 15, idx),
                impact
            )

    @role(operator)
    def test_sanity_rates(self):
        token_addresses = [token.address for token in tokens]
        sanity_rates = [Web3.toWei(0.01, 'ether') for _ in tokens]
        self.reserve.set_sanity_rates(token_addresses, sanity_rates)

        self.reserve.change_account(admin)
        zero_diff = [0 for _ in tokens]
        self.reserve.set_reasonable_diff(token_addresses, zero_diff)

        self.assertEqual(
            sanity_rates[0],
            self.reserve.get_sanity_rates(
                src=token_addresses[0],
                dst=Web3.toChecksumAddress(
                    '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
                )
            )
        )

    @role(admin)
    def test_reasonable_diff(self):
        token_addresses = [token.address for token in tokens]
        reasonable_diff = [int(random.random() * 1000) for _ in tokens]

        self.reserve.set_reasonable_diff(token_addresses, reasonable_diff)

        self.assertEqual(
            reasonable_diff[0],
            self.reserve.get_reasonable_diff_in_bps(token_addresses[0])
        )
