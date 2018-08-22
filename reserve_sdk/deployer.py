import time

from web3 import Web3

from .contract_code import (
    RESERVE_CODE, CONVERSION_RATES_CODE, SANITY_RATES_CODE)
from .addresses import Addresses
from .contract import Reserve


class Deployer:
    """Deployer is used for deploying new KyberNetwork reserve contracts."""

    def __init__(self, provider, account):
        """Create a deployer instance given a provider.
        """
        self.__provider = provider
        self.__w3 = Web3(provider)
        self.__w3.eth.accounts.append(account)
        self.__w3.eth.defaultAccount = account.address
        self.__acct = account

    def deploy(self, network_addr):
        """Deploy new reserve and pricing contracts.
        Args:
            network_addr: the address of network contracts.

        Steps:
            1. Deploy ConversionRates contract
            2. Deploy Reserve contract

        Returns:
            addresses: deployed reserve addresses set.
        """

        conversion_rates_addr = self.__deploy_contract(
            abi=CONVERSION_RATES_CODE.abi,
            bytecode=CONVERSION_RATES_CODE.bin,
            contract_args=[self.__acct.address]
        )

        reserve_addr = self.__deploy_contract(
            abi=RESERVE_CODE.abi,
            bytecode=RESERVE_CODE.bin,
            contract_args=[network_addr,
                           conversion_rates_addr,
                           self.__acct.address]
        )

        sanity_rates_addr = self.__deploy_contract(
            abi=SANITY_RATES_CODE.abi,
            bytecode=SANITY_RATES_CODE.bin,
            contract_args=[self.__acct.address]
        )

        addresses = Addresses(
            reserve_addr,
            conversion_rates_addr,
            sanity_rates_addr
        )

        """
        TODO
        Reserve
        - Whitelist deposit address: reserve approve withdraw address
        - Set permissions
        Rates:
        - Add token to conversion_rates_addr
        - Set valid duration block
        - Set reserve address [DONE]
        - Set control info
        - Enable token trade
        - Add temporary operator
        - Set imbalance function to 0
        - Remove temporary operator
        - Set permissions
        """

        # Link addresses between reserve contracts
        reserve = Reserve(self.__provider, self.__acct, addresses)
        reserve.conversion_rates_contract.set_reserve_address(reserve_addr)
        reserve.reserve_contract.set_contracts(
            network_addr,
            conversion_rates_addr,
            sanity_rates_addr
        )

        return addresses

    def __deploy_contract(self, abi, bytecode, contract_args):
        """Deploy a single smart contract
        Args:
            abi: contract's abi
            bytecode: contract's bytecode
            contract_args: arguments to construct the contract
        Returns: the deployed smart contract address
        """
        contract = self.__w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract.constructor(*contract_args).transact()
        tx_receipt = self.__w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt['contractAddress']
