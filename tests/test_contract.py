import unittest
import json
import os
from functools import wraps

from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer, ReserveContract, Reserve
from reserve_sdk.utils import deploy_contract
from reserve_sdk.contract_code import ContractCode
from reserve_sdk.token import Token


NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'

backend = PyEVMBackend()
tester = EthereumTester(backend)
provider = EthereumTesterProvider(tester)
w3 = Web3(provider)

test_accts = []
for key in backend.account_keys:
    test_accts.append(w3.eth.account.privateKeyToAccount(key.to_hex()))

deployer, admin_1, admin_2, operator, alerter = test_accts[:5]
admin = deployer

# deploy reserve contracts
d = Deployer(provider, deployer)
addresses = d.deploy(NETWORK_ADDR)
reserve = Reserve(provider, deployer, addresses)

# deploy test tokens
token_code_file_path = os.path.join(os.path.dirname(__file__),
                                    'erc20_token_code.json')

with open(token_code_file_path) as f:
    token_code = json.load(f)
    erc20_token_code = ContractCode(
        abi=token_code['abi'], bin=token_code['bytecode'])

tokens = []
for i in range(3):
    token_addr = deploy_contract(
        w3,
        deployer,
        erc20_token_code,
        [str(i), str(i), 18]
    )
    tokens.append(Token(token_addr, erc20_token_code.abi, w3, deployer))


def role(account):
    """ Set specific account to execute contract function.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kargs):
            self.contract.change_account(account)
            return func(self, *args, **kargs)

        return wrapper
    return decorator


class TestBaseContract(unittest.TestCase):

    def setUp(self):
        self.contract = reserve.reserve_contract

    def test_contract_admin_is_sender(self):
        self.assertEqual(self.contract.admin(), deployer.address)

    def test_contract_pending_admin(self):
        self.assertNotEqual(self.contract.pending_admin(), '')

    def test_get_contract_operators(self):
        self.assertEqual(type(self.contract.operators()), list)

    def test_get_contract_alerters(self):
        self.assertEqual(type(self.contract.alerters()), list)

    def test_transfer_admin(self):
        self.contract.transfer_admin(admin_2.address)
        self.assertIn(admin_2.address, self.contract.pending_admin())

    def test_claim_admin(self):
        """
        Deployer is the current admin.
        This test will transfer admin to admin_1, check if admin_1 in pending
        admin. Then admin_1 claim admin to be the contract admin.
        At last, the admin_1 transfer admin back to deployer.
        """
        self.contract.transfer_admin(admin_1.address)
        self.assertIn(admin_1.address, self.contract.pending_admin())
        self.contract.change_account(admin_1)
        self.contract.claim_admin()
        self.assertEqual(self.contract.admin(), admin_1.address)

        self.contract.transfer_admin(deployer.address)
        self.contract.change_account(deployer)
        self.contract.claim_admin()
        self.assertEqual(self.contract.admin(), deployer.address)

    def test_add_and_remove_operator(self):
        # test add new operator to contract
        self.contract.add_operator(operator.address)
        self.assertIn(operator.address, self.contract.operators())

        # test remove operator to contract
        self.contract.remove_operator(operator.address)
        self.assertNotIn(operator.address, self.contract.operators())

    def test_add_and_remove_alerter(self):
        # add new alerter to contract
        self.contract.add_alerter(alerter.address)
        self.assertIn(alerter.address, self.contract.alerters())

        # remove the alerter from contract
        self.contract.remove_alerter(alerter.address)
        self.assertNotIn(alerter.address, self.contract.alerters())


class TestReserveContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reserve.reserve_contract.add_operator(operator.address)
        reserve.reserve_contract.add_alerter(alerter.address)
        for token in tokens:
            token.transfer(addresses.reserve, 5000 * 10**18)

    def setUp(self):
        self.contract = reserve.reserve_contract

    def test_get_balance(self):
        self.assertIsInstance(
            self.contract.get_balance(tokens[0].address),
            int
        )

    def test_link_with_new_contract_addresses(self):
        new_addresses = d.deploy(NETWORK_ADDR)

        self.contract.set_contracts(
            NETWORK_ADDR,
            new_addresses.conversion_rates,
            new_addresses.sanity_rates
        )

        self.assertEqual(
            self.contract.get_network_address(),
            NETWORK_ADDR
        )
        self.assertEqual(
            self.contract.get_conversion_rates_address(),
            new_addresses.conversion_rates
        )
        self.assertEqual(
            self.contract.get_sanity_rates_address(),
            new_addresses.sanity_rates
        )

    def test_approve_and_disapprove_withdraw_address(self):
        token = tokens[0]
        # Check the operator is not approved to withdraw token yet.
        self.assertFalse(self.contract.approved_withdraw_addresses(
            operator.address, token.address
        ))
        self.contract.approve_withdraw_address(
            operator.address, token.address
        )
        self.assertTrue(self.contract.approved_withdraw_addresses(
            operator.address, token.address
        ))
        self.contract.disapprove_withdraw_address(
            operator.address, token.address
        )
        self.assertFalse(self.contract.approved_withdraw_addresses(
            operator.address, token.address
        ))

    def test_withdraw_token_from_reserve(self):
        token = tokens[0]
        blc = token.balanceOf(operator.address)
        self.contract.change_account(deployer)
        self.contract.approve_withdraw_address(
            operator.address, token.address
        )
        # Only contract operator can withdraw token.
        self.contract.change_account(operator)
        tx = self.contract.withdraw(token.address, 10, operator.address)
        new_blc = token.balanceOf(operator.address)
        self.assertEqual(new_blc, blc + 10)

    def test_enable_trade_by_contract_admin(self):
        self.assertFalse(self.contract.trade_enabled())
        self.contract.enable_trade()
        self.assertTrue(self.contract.trade_enabled())

    @role(alerter)
    def test_disable_trade_by_alerter(self):
        self.contract.disable_trade()
        self.assertFalse(self.contract.trade_enabled())
        self.contract.change_account(deployer)


class TestConversionRatesContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reserve.conversion_rates_contract.add_operator(operator.address)
        reserve.conversion_rates_contract.set_valid_rate_duration_in_blocks(60)
        reserve.conversion_rates_contract.add_new_token(
            token=tokens[0].address,
            minimal_record_resolution=int(0.0001 * 10**18),
            max_per_block_imbalance=int(439.79 * 10**18),
            max_total_imbalance=int(922.36 * 10**18)
        )

        reserve.conversion_rates_contract.add_new_token(
            token=tokens[1].address,
            minimal_record_resolution=int(0.0001 * 10**18),
            max_per_block_imbalance=int(439.79 * 10**18),
            max_total_imbalance=int(922.36 * 10**18)
        )

    def setUp(self):
        self.contract = reserve.conversion_rates_contract

    @role(deployer)
    def test_link_with_new_reserve_contract(self):
        new_address = d.deploy(NETWORK_ADDR)

        self.contract.set_reserve_address(new_address.reserve)
        self.assertEqual(
            self.contract.get_reserve_address(),
            new_address.reserve
        )

    @role(operator)
    def test_basic_rates(self):
        token_1, token_2 = tokens[:2]

        # set token base rates
        token_addresses = [token_1.address, token_2.address]
        buy_rates = [500 * 10**18, 400 * 10**18]
        sell_rates = [182 * 10**18, 232 * 10**18]
        self.contract.set_rates(token_addresses, buy_rates, sell_rates)

        self.assertEqual(
            self.contract.get_basic_rate(token_1.address, buy=True),
            buy_rates[0]
        )
        self.assertEqual(
            self.contract.get_basic_rate(token_2.address, buy=True),
            buy_rates[1]
        )
        self.assertEqual(
            self.contract.get_basic_rate(token_1.address, buy=False),
            sell_rates[0]
        )
        self.assertEqual(
            self.contract.get_basic_rate(token_2.address, buy=False),
            sell_rates[1]
        )

        # set pricing step function
        self.contract.set_qty_step_function(
            token_1.address, [0], [0], [0], [0]
        )
        self.contract.set_imbalance_step_function(
            token_1.address, [0], [0], [0], [0]
        )

        self.assertEqual(
            self.contract.get_buy_rate(token_1.address, qty=1),
            buy_rates[0]
        )
        self.assertEqual(
            self.contract.get_sell_rate(token_1.address, qty=1),
            sell_rates[0]
        )

    @role(operator)
    def test_qty_step_function(self):
        token = tokens[0]
        x_buy = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_buy = [0, -30, -60, -80]
        x_sell = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_sell = [0, -30, -60, -80]
        self.contract.set_qty_step_function(
            token.address,
            x_buy,
            y_buy,
            x_sell,
            y_sell,
        )

        self.assertEqual(
            self.contract.get_step_function_data(token.address, 0, 0),
            len(x_buy)
        )
        for idx, step in enumerate(x_buy):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 1, idx),
                step
            )
        self.assertEqual(
            self.contract.get_step_function_data(token.address, 2, 0),
            len(y_buy)
        )
        for idx, impact in enumerate(y_buy):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 3, idx),
                impact
            )

        self.assertEqual(
            self.contract.get_step_function_data(token.address, 4, 0),
            len(x_sell)
        )
        for idx, step in enumerate(x_sell):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 5, idx),
                step
            )
        self.assertEqual(
            self.contract.get_step_function_data(token.address, 6, 0),
            len(y_sell)
        )
        for idx, impact in enumerate(y_sell):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 7, idx),
                impact
            )

    @role(operator)
    def test_imbalance_step_function(self):
        token = tokens[0]

        x_buy = [100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18]
        y_buy = [0, -30, -60, -80]
        x_sell = [300 * 10**18, 200 * 10**18, 100 * 10**18, 0]
        y_sell = [-70, -50, -25, 0]
        self.contract.set_imbalance_step_function(
            token.address,
            x_buy,
            y_buy,
            x_sell,
            y_sell,
        )

        self.assertEqual(
            self.contract.get_step_function_data(token.address, 8, 0),
            len(x_buy)
        )
        for idx, step in enumerate(x_buy):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 9, idx),
                step
            )
        self.assertEqual(
            self.contract.get_step_function_data(token.address, 10, 0),
            len(y_buy)
        )
        for idx, impact in enumerate(y_buy):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 11, idx),
                impact
            )

        self.assertEqual(
            self.contract.get_step_function_data(token.address, 12, 0),
            len(x_sell)
        )
        for idx, step in enumerate(x_sell):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 13, idx),
                step
            )
        self.assertEqual(
            self.contract.get_step_function_data(token.address, 14, 0),
            len(y_sell)
        )
        for idx, impact in enumerate(y_sell):
            self.assertEqual(
                self.contract.get_step_function_data(token.address, 15, idx),
                impact
            )

    @role(operator)
    def test_rate_with_qty_step_function(self):
        token = tokens[0]

        self.contract.set_rates(
            token_addresses=[token.address],
            buy_rates=[500 * 10**18],
            sell_rates=[182 * 10**18]
        )
        self.contract.set_qty_step_function(
            token=token.address,
            x_buy=[100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18],
            y_buy=[0, -30, -60, -80],
            x_sell=[100 * 10**18, 200 * 10**18, 300 * 10**18, 500 * 10**18],
            y_sell=[0, -30, -60, -80],
        )
        self.contract.set_imbalance_step_function(
            token.address, [0], [0], [0], [0]
        )

        # get sell rate, need to pass token qty
        self.assertEqual(
            self.contract.get_sell_rate(token.address, qty=(90 * 10**18)),
            182 * 10**18
        )
        self.assertEqual(
            self.contract.get_sell_rate(token.address, qty=(150 * 10**18)),
            182 * 10**18 * (1 - 30 * 0.01 / 100)
        )

        # get sell rate, need to pass eth qty
        self.assertEqual(
            self.contract.get_buy_rate(token.address, qty=int(0.1 * 10**18)),
            500 * 10**18
        )
        self.assertEqual(
            self.contract.get_buy_rate(token.address, qty=int(0.3 * 10**18)),
            500 * 10**18 * (1 - 30 * 0.01 / 100)
        )

    @unittest.skip('need to perform trade action')
    def test_rate_with_imbalance_step_function(self):
        pass
