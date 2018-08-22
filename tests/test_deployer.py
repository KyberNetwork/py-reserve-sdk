import unittest

from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer, Reserve


NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'


class TestDeployer(unittest.TestCase):

    def setUp(self):
        backend = PyEVMBackend()
        tester = EthereumTester(backend)
        self.provider = EthereumTesterProvider(tester)

        private_key = backend.account_keys[0].to_hex()
        self.w3 = Web3(self.provider)
        self.account = self.w3.eth.account.privateKeyToAccount(private_key)

        d = Deployer(self.provider, self.account)
        self.addresses = d.deploy(network_addr=NETWORK_ADDR)

    def test_deployed_addresses_is_valid(self):
        self.assertTrue(self.w3.isAddress(self.addresses.conversion_rates))
        self.assertTrue(self.w3.isAddress(self.addresses.reserve))
        self.assertTrue(self.w3.isAddress(self.addresses.sanity_rates))

    def test_reserve_contracts_linked(self):
        reserve = Reserve(self.provider, self.account, self.addresses)

        # linked address in reserve contract
        self.assertEqual(
            reserve.reserve_contract.get_network_address(),
            NETWORK_ADDR
        )
        self.assertEqual(
            reserve.reserve_contract.get_conversion_rates_address(),
            self.addresses.conversion_rates
        )
        self.assertEqual(
            reserve.reserve_contract.get_sanity_rates_address(),
            self.addresses.sanity_rates
        )

        # linked address in conversion rates contract
        self.assertEqual(
            reserve.conversion_rates_contract.get_reserve_address(),
            self.addresses.reserve
        )
