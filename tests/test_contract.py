import unittest

from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer, ReserveContract, Reserve


NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'

backend = PyEVMBackend()
tester = EthereumTester(backend)
provider = EthereumTesterProvider(tester)
w3 = Web3(provider)

test_accts = []
for key in backend.account_keys:
    test_accts.append(w3.eth.account.privateKeyToAccount(key.to_hex()))

deployer, admin_1, admin_2, operator, alerter = test_accts[:5]

# deploy reserve contracts
d = Deployer(provider, deployer)
addresses = d.deploy(NETWORK_ADDR)
reserve = Reserve(provider, deployer, addresses)


class TestBaseContract(unittest.TestCase):

    def setUp(self):
        self.contract = reserve.reserve_contract
        self.deployer = deployer

    def test_contract_admin_is_sender(self):
        self.assertEqual(self.contract.admin(), self.deployer.address)

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
        Deployer is the current admin. This test will transfer admin to admin_1,
        check if admin_1 in pending admin. Then admin_1 claim admin to be the
        contract admin. At last, the admin_1 transfer admin back to deployer.
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

    def setUp(self):
        self.contract = reserve.reserve_contract
        self.deployer = deployer

    def test_reserve_contract_disable_trade_by_default(self):
        self.assertIs(self.contract.trade_enabled(), None)

    def test_reserve_have_no_eth(self):
        eth_addr = Web3.toChecksumAddress(
            '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        self.assertEqual(self.contract.get_balance(eth_addr), 0)

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


class TestConversionRatesContract(unittest.TestCase):

    def setUp(self):
        self.contract = reserve.conversion_rates_contract
        self.deployer = deployer

    def test_link_with_new_reserve_contract(self):
        new_address = d.deploy(NETWORK_ADDR)

        self.contract.set_reserve_address(new_address.reserve)
        self.assertEqual(
            self.contract.get_reserve_address(),
            new_address.reserve
        )
