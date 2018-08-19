class BaseContract:
    """BaseContract contains common methods for all contracts of a KyberNetwork 
    reserve.
    """

    def __init__(self, provider, address):
        """Create new BaseContract instance."""
        raise NotImplementedError

    def admin(self):
        """Get current admin address of contract."""
        raise NotImplementedError

    def pending_admin(self):
        """Get pending admin address of contract.
        An admin address is placed in pending if it is tranfered but 
        hasnt been claimed yet.
        """
        raise NotImplementedError

    def operators(self):
        """Get operator addresses of contract."""
        raise NotImplementedError

    def alerters(self):
        """Get alerter addresses of contract."""
        raise NotImplementedError

    def transfer_admin(self, address):
        """Transfer admin privilege to given address.
        Args:
            address: new admin address
        """
        raise NotImplementedError

    def claim_admin(self):
        """Claim admin privilege.
        The account address should be in already placed in pendingAdmin for
        this to works.
        """
        raise NotImplementedError

    def add_operator(self, address):
        """Add given address to operators list.
        Args:
            address: new operator address
        """
        raise NotImplementedError

    def remove_operator(self, address):
        """Remove given address from operators list.
        Args:
            address: operator address
        """
        raise NotImplementedError

    def add_alerter(self, address):
        """Add given address to alerters list.
        Args:
            address: new alerter address
        """
        raise NotImplementedError

    def remove_alerter(self, address):
        """Remove given address from alerters list.
        Args:
            address: alerter address
        """
        raise NotImplementedError


class ReserveContract(BaseContract):
    """ReserveContract represent the KyberNetwork reserve smart contract."""

    def __init__(self, address):
        """Create ReserveContract instance given an address."""
        raise NotImplementedError

    def trade_enabled(self):
        """Return true if the reserve is tradable."""
        raise NotImplementedError

    def approved_withdraw_address(self, address):
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
        raise NotImplementedError

    def enable_trade(self):
        """Enable trading feature for reserve contract."""
        raise NotImplementedError

    def disable_trade(self):
        """Disable trading feature for reserve contract."""
        raise NotImplementedError

    def approve_withdrawal(self, address, token):
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


class ConversionRatesContract(BaseContract):
    """ConversionRatesContract represents the KyberNetwork conversion rates
    smart contract.
    """

    def __init__(self, address):
        """Create new ConversionRatesContract instance.
        Args:
            address: the address of smart contract
        """
        raise NotImplementedError

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


class SanityRatesContract(BaseContract):
    """SanityRatesContract represents the KyberNetwork sanity rates contract.
    This contract prevent unusual rates from conversion rates contract to be
    used.
    """

    def __init__(self, address):
        """Create new SanityRatesContract instance."""
        super().__init__(address)


class Reserve:
    """Reserve represent a KyberNetwork reserve SDK.
    It containts method to interact with reserve and pricing contract, 
    including:
    - Deploy new contract
    - Reserve operations
    - Get/Set pricing
    - Withdraw funds
    """

    def __init__(self, provider, addresses):
        """Create a Reserve instance.
        Args:
            provider: web3 provider
            addresses: addresses of deployed smart contracts
        """
        self.reserve_contract = ReserveContract(provider, addresses.reserve)
        self.conversion_rates_contract = ConversionRatesContract(
            provider, addresses.conversion_rates)
        self.sanity_rate = SanityRatesContract(
            provider, addresses.sanity_rates
        )
