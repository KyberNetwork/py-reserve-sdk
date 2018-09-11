import time

from web3 import Web3

from .contract_code import (
    RESERVE_CODE, CONVERSION_RATES_CODE, SANITY_RATES_CODE)
from .addresses import Addresses
from .utils import deploy_contract


class Deployer:
    """Deployer is used for deploying new KyberNetwork reserve contracts."""

    def __init__(self, provider, account):
        """Create a deployer instance given a provider.
        """
        self.__provider = provider
        self.__w3 = Web3(provider)
        self.__w3.eth.defaultAccount = account.address
        self.__acct = account

    def deploy(self, network_addr):
        """Deploy new reserve and pricing contracts.

        :arg str network_addr: The address of network contract
        :return: :class:`Reserve Contract Addresses <reserve_sdk.Addresses>`
        """

        conversion_rates_addr = deploy_contract(
            self.__w3,
            self.__acct,
            CONVERSION_RATES_CODE,
            [self.__acct.address]
        )

        reserve_addr = deploy_contract(
            self.__w3,
            self.__acct,
            RESERVE_CODE,
            [network_addr, conversion_rates_addr, self.__acct.address]
        )

        sanity_rates_addr = deploy_contract(
            self.__w3,
            self.__acct,
            SANITY_RATES_CODE,
            [self.__acct.address]
        )

        return Addresses(
            reserve_addr,
            conversion_rates_addr,
            sanity_rates_addr
        )
