import unittest

from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer


NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'


class TestDeployer(unittest.TestCase):

    def setUp(self):
        self.provider = EthereumTesterProvider()
        w3 = Web3(self.provider)
        self.account = w3.eth.account.create()

    def test_deploy_success(self):
        d = Deployer(self.provider, self.account)
        addresses = d.deploy(network_addr=NETWORK_ADDR)
        self.assertEqual(addresses.conversion_rates,
                         '0xa0Beb7081fDaF3ed157370836A85eeC20CEc9e04')
        self.assertEqual(addresses.reserve,
                         '0xa0Beb7081fDaF3ed157370836A85eeC20CEc9e04')
        self.assertEqual(addresses.sanity_rates, '')
