import time

from web3 import Web3

from .contract_code import RESERVE_CODE, CONVERSION_RATES_CODE
from .addresses import Addresses


class Deployer:
    """Deployer is used for deploying new KyberNetwork reserve contracts."""

    def __init__(self, provider, account):
        """Create a deployer instance given a provider.
        """
        self.__w3 = Web3(provider)
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

        return Addresses(reserve_addr, conversion_rates_addr, '')

    def __deploy_contract(self, abi, bytecode, contract_args):
        """Deploy a single smart contract
        Args:
            abi: contract's abi
            bytecode: contract's bytecode
            contract_args: arguments to construct the contract
        Returns: the deployed smart contract address
        TODO:
            - estimate gas
            - generate gas price
        """
        contract = self.__w3.eth.contract(abi=abi, bytecode=bytecode)
        data = contract.constructor(*contract_args).buildTransaction({
            'from': self.__acct.address,
            'nonce': self.__w3.eth.getTransactionCount(self.__acct.address),
            'gas': 4000000,
            'gasPrice': self.__w3.toWei('21', 'gwei')
        })
        signed = self.__acct.signTransaction(data)
        tx_hash = self.__w3.eth.sendRawTransaction(signed.rawTransaction)

        # Wait for transaction receipt.
        while True:
            tx_receipt = self.__w3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                return tx_receipt['contractAddress']
            else:
                time.sleep(1)
