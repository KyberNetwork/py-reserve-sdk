import unittest

from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer


NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'


class TestDeployer(unittest.TestCase):

    def setUp(self):
        backend = PyEVMBackend()
        tester = EthereumTester(backend)
        self.provider = EthereumTesterProvider(tester)
        
        private_key = backend.account_keys[0].to_hex()
        w3 = Web3(self.provider)
        self.account = w3.eth.account.privateKeyToAccount(private_key)

    def test_deploy_success(self):
        d = Deployer(self.provider, self.account)
        addresses = d.deploy(network_addr=NETWORK_ADDR)
        self.assertNotEqual(addresses.conversion_rates, '')
        self.assertNotEqual(addresses.reserve, '')
        self.assertNotEqual(addresses.sanity_rates, '')
