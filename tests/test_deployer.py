import unittest

from web3 import Web3

from reserve_sdk import Deployer
from .utils import (
    NETWORK_ADDR, provider, test_accounts
)


admin = test_accounts[0]


class TestDeployer(unittest.TestCase):

    def setUp(self):
        d = Deployer(provider, admin)
        self.addresses = d.deploy(network_addr=NETWORK_ADDR)

    def test_deployed_addresses_is_valid(self):
        self.assertTrue(Web3.isAddress(self.addresses.conversion_rates))
        self.assertTrue(Web3.isAddress(self.addresses.reserve))
        self.assertTrue(Web3.isAddress(self.addresses.sanity_rates))
