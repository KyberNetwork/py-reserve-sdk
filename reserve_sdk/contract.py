from web3 import Web3

from .contract_code import RESERVE_CODE, CONVERSION_RATES_CODE, SANITY_RATES_CODE


class BaseContract:
    """BaseContract contains common methods for all contracts of a KyberNetwork 
    reserve.
    """

    def __init__(self, provider, account, address, abi):
        """Create new BaseContract instance."""
        self.w3 = Web3(provider)
        self.w3.eth.accounts.append(account)
        self.w3.eth.defaultAccount = account.address
        self.contract = self.w3.eth.contract(address=address, abi=abi)

    def admin(self):
        """Get current admin address of contract."""
        return self.contract.functions.admin().call()

    def pending_admin(self):
        """Get pending admin address of contract.
        An admin address is placed in pending if it is tranfered but 
        hasnt been claimed yet.
        """
        return self.contract.functions.pendingAdmin().call()

    def operators(self):
        """Get operator addresses of contract."""
        return self.contract.functions.getOperators().call()

    def alerters(self):
        """Get alerter addresses of contract."""
        return self.contract.functions.getAlerters().call()

    def transfer_admin(self, address):
        """Transfer admin privilege to given address.
        Args:
            address: new admin address
        Returns transaction hash.
        """
        return self.contract.functions.transferAdmin(address).transact()

    def claim_admin(self):
        """Claim admin privilege.
        The account address should be in already placed in pendingAdmin for
        this to works.
        Returns transaction hash.
        """
        return self.contract.functions.claimAdmin().transact()

    def add_operator(self, address):
        """Add given address to operators list.
        Args:
            address: new operator address
        Returns transaction hash.
        """
        return self.contract.functions.addOperator(address).transact()

    def remove_operator(self, address):
        """Remove given address from operators list.
        Args:
            address: operator address
        Returns transaction hash.
        """
        return self.contract.functions.removeOperator(address).transact()

    def add_alerter(self, address):
        """Add given address to alerters list.
        Args:
            address: new alerter address
        Returns transaction hash.
        """
        return self.contract.functions.addAlerter(address).transact()

    def remove_alerter(self, address):
        """Remove given address from alerters list.
        Args:
            address: alerter address
        Returns transaction hash.
        """
        return self.contract.functions.removeAlerter(address).transact()

    def change_account(self, account):
        """TODO: need to review this behaviour. Client could init an other
        instance of contract with new account.
        """
        self.w3.eth.accounts.append(account)
        self.w3.eth.defaultAccount = account.address


class ReserveContract(BaseContract):
    """ReserveContract represent the KyberNetwork reserve smart contract."""

    def __init__(self, provider, account, address):
        """Create ReserveContract instance given an address."""
        super().__init__(provider, account, address, RESERVE_CODE.abi)

    def trade_enabled(self):
        """Return true if the reserve is tradable."""
        self.contract.functions.tradeEnabled().call()

    def approved_withdraw_addresses(self, address):
        """Return true if the given address is allowed to withdraw from reserve
        contract.
        """
        raise NotImplementedError

    def get_balance(self, token):
        """Return balance of given token.
        Args:
            token: address of token to check balance
        Return:
            The balance of token.
        """
        return self.contract.functions.getBalance(token).call()

    def enable_trade(self):
        """Enable trading feature for reserve contract."""
        raise NotImplementedError

    def disable_trade(self):
        """Disable trading feature for reserve contract."""
        raise NotImplementedError

    def approve_withdraw_address(self, address, token):
        """Allow given address to withdraw a specific token from reserve.
        Args:
            address: address to allow withdrawal
            token: token address
        """
        raise NotImplementedError

    def disapprove_withdrawal(self, address, token):
        """Disallow an address to withdraw a specific token from reserve
        Args:
            address: address to disallow withdrawal
            token: token address
        """
        raise NotImplementedError

    def withdraw(self, token, amount, dest):
        """Withdraw token from reserve to destination address.
        Args:
            token: token address
            amount: amount of token to withdraw
            dest: destination address to receive the token
        """
        raise NotImplementedError

    def set_contracts(self, network, rates, sanity_rates):
        """Update relevant address to reserve.
        Args:
            network: the address of KyberNetwork
            rates: the address of conversions rates contract
            sanity_rates: the address of sanity rates contract
        """
        return self.contract.functions.setContracts(
            network, rates, sanity_rates).transact()

    def get_sanity_rates_address(self):
        return self.contract.functions.sanityRatesContract().call()

    def get_network_address(self):
        return self.contract.functions.kyberNetwork().call()

    def get_conversion_rates_address(self):
        return self.contract.functions.conversionRatesContract().call()


class ConversionRatesContract(BaseContract):
    """ConversionRatesContract represents the KyberNetwork conversion rates
    smart contract.
    """

    def __init__(self, provider, account, address):
        """Create new ConversionRatesContract instance.
        Args:
            address: the address of smart contract
        """
        super().__init__(provider, account, address, CONVERSION_RATES_CODE.abi)

    def get_buy_rate(self, token, qty):
        """Return the buying rate (ETH based). The rate might be vary with
        different quantity.
        TODO: check if block_number is required
        Args:
            token: token address
            qty: the amount to buy
        """
        raise NotImplementedError

    def get_sell_rate(self, token, qty):
        """Return the selling rate (ETH based). The rate might be vary with
        different quantity.
        TODO: check if block_number is needed.
        Args:
            token: token address
            qty: the amount of token to sell
        """
        raise NotImplementedError

    def set_buy_rate(self, token, rate):
        """Place the buying rate for given token.
        Args:
            token: the token address
            rate: new rate to set
        """
        raise NotImplementedError

    def set_sell_rate(self, token, rate):
        """Place the selling rate for given token.
        Args:
            token: the token address
            rate: new rate to set
        """
        raise NotImplementedError

    def set_reserve_address(self, reserve_addr):
        """Update reserve address."""
        return self.contract.functions.setReserveAddress(reserve_addr).transact()

    def get_reserve_address(self):
        return self.contract.functions.reserveContract().call()


class SanityRatesContract(BaseContract):
    """SanityRatesContract represents the KyberNetwork sanity rates contract.
    This contract prevent unusual rates from conversion rates contract to be
    used.
    """

    def __init__(self, provider, account, address):
        """Create new SanityRatesContract instance."""
        super().__init__(provider, account, address, SANITY_RATES_CODE.abi)


class Reserve:
    """Reserve represent a KyberNetwork reserve SDK.
    It containts method to interact with reserve and pricing contract, 
    including:
    - Deploy new contract
    - Reserve operations
    - Get/Set pricing
    - Withdraw funds
    """

    def __init__(self, provider, account, addresses):
        """Create a Reserve instance.
        Args:
            provider: web3 provider
            addresses: addresses of deployed smart contracts
        """
        self.reserve_contract = ReserveContract(
            provider, account, addresses.reserve)
        self.conversion_rates_contract = ConversionRatesContract(
            provider, account, addresses.conversion_rates)
        self.sanity_rate_contract = SanityRatesContract(
            provider, account, addresses.sanity_rates
        )
