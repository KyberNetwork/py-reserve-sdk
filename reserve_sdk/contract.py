from collections import namedtuple
from concurrent import futures

from web3 import Web3

from .contract_code import (
    RESERVE_CODE, CONVERSION_RATES_CODE, SANITY_RATES_CODE)
from .utils import hexlify, call_contract


"""Show token position in the compact data."""
TokenIndex = namedtuple('TokenIndex', ('array_idx', 'field_idx'))
CompactData = namedtuple('CompactData', ('base', 'compact', 'base_changed'))


def get_compact_data(rate, base):
    """
    Calculate compact data from new rate and base rate.

    Args:
        rate: value of new sell/buy price
        base: value of current sell/buy price at contract

    Returns:
        compact_data which include new base rate & compact value which is the
        different between rate and base in bps unit.
    """
    if base == 0:
        return CompactData(rate, 0, base_changed=(base != rate))

    compact = int((rate/base - 1) * 1000)
    if compact <= -128 or compact >= 127:  # not fit in a byte
        return CompactData(rate, 0, base_changed=True)
    else:
        # handle negative value to convert to byte
        if compact < 0:
            compact += 256
        return CompactData(base, compact, base_changed=False)


def build_compact_price(prices, token_indices):
    """Prepare compact price to setCompactData through pricing contract.

    Args:
        prices: price change in bps unit
        token_indices: index of token in compact data on contract

    Return:
        buy: buy prices change in bps unit, encoded in hex
        sell: sell prices change in bps unit, encoded in hex
        indices: the index of block token in compact data on contract
    """
    result = {}

    for p in prices:
        array_idx = token_indices[p['token']].array_idx
        field_idx = token_indices[p['token']].field_idx

        if array_idx not in result:
            result[array_idx] = {
                'buy': [0] * 14,
                'sell': [0] * 14
            }

        result[array_idx]['buy'][field_idx] = p['compact_buy']
        result[array_idx]['sell'][field_idx] = p['compact_sell']

    buy = []
    sell = []
    indices = []

    for k, v in result.items():
        buy.append(hexlify(v['buy']))
        sell.append(hexlify(v['sell']))
        indices.append(k)

    return buy, sell, indices


class BaseContract:
    """BaseContract contains common methods for all contracts of a KyberNetwork
    reserve.
    """

    def __init__(self, provider, account, address, abi):
        """Create new BaseContract instance."""
        self.w3 = Web3(provider)
        self.contract = self.w3.eth.contract(address=address, abi=abi)
        self.account = account
        self.w3.eth.defaultAccount = account.address

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

        :arg str address: New admin address
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.transferAdmin(address)
        )

    def claim_admin(self):
        """Claim admin privilege.
        The account address should be in already placed in pendingAdmin for
        this to works.
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.claimAdmin()
        )

    def add_operator(self, address):
        """Add given address to operators list.

        :arg str address: New operator address
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.addOperator(address)
        )

    def remove_operator(self, address):
        """Remove given address from operators list.

        :arg str address: Operator address
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.removeOperator(address)
        )

    def add_alerter(self, address):
        """Add given address to alerters list.

        :arg str address: The new alerter address
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.addAlerter(address)
        )

    def remove_alerter(self, address):
        """Remove given address from alerters list.

        :arg str address: Alerter address
        :return: The transaction hash
        """
        return self.call_contract_func(
            self.contract.functions.removeAlerter(address)
        )

    def change_account(self, account):
        """Set account to sign tx when execute contract functions."""
        self.account = account
        self.w3.eth.defaultAccount = account.address

    def call_contract_func(self, func):
        """Send transaction to execute contract function.

        :arg function func: The contract function with parameters
        :return: The transaction hash
        """
        return call_contract(self.w3, self.account, func)


class ReserveContract(BaseContract):
    """ReserveContract represent the KyberNetwork reserve smart contract."""

    def __init__(self, provider, account, address):
        """Create ReserveContract instance given an address."""
        super().__init__(provider, account, address, RESERVE_CODE.abi)

    def trade_enabled(self):
        """Return true if the reserve is tradable."""
        return self.contract.functions.tradeEnabled().call()

    def approved_withdraw_addresses(self, address, token):
        """Return true if the given address is allowed to withdraw from reserve
        contract.

        :arg str address: Account address
        :arg str token: The Token address
        """
        sha = Web3.soliditySha3(['address', 'address'], [token, address])
        return self.contract.functions.approvedWithdrawAddresses(sha).call()

    def get_balance(self, token):
        """Return balance of given token.

        :arg str token: Token address
        :return: The balance of token
        """
        return self.contract.functions.getBalance(token).call()

    def enable_trade(self):
        """Enable trading feature for reserve contract."""
        return self.call_contract_func(
            self.contract.functions.enableTrade()
        )

    def disable_trade(self):
        """Disable trading feature for reserve contract."""
        return self.call_contract_func(
            self.contract.functions.disableTrade()
        )

    def approve_withdraw_address(self, address, token):
        """Allow given address to withdraw a specific token from reserve.

        :arg str address: Address to allow withdrawal
        :arg str token: Token address
        """
        return self.call_contract_func(
            self.contract.functions.approveWithdrawAddress(
                token, address, True
            )
        )

    def disapprove_withdraw_address(self, address, token):
        """Disallow an address to withdraw a specific token from reserve.

        :arg str address: Address to disallow withdrawal
        :arg str token: Token address
        """
        return self.call_contract_func(
            self.contract.functions.approveWithdrawAddress(
                token, address, False
            )
        )

    def withdraw(self, token, amount, dest):
        """Withdraw token from reserve to destination address.

        :arg str token: Token address
        :arg int amount: Amount of token to withdraw
        :arg str dest: Destination address to receive the token
        """
        return self.call_contract_func(
            self.contract.functions.withdraw(token, amount, dest)
        )

    def set_contracts(self, network, rates, sanity_rates):
        """Update relevant address to reserve.

        :arg str network: The address of KyberNetwork
        :arg str rates: The address of conversions rates contract
        :arg str sanity_rates: The address of sanity rates contract
        """
        return self.call_contract_func(
            self.contract.functions.setContracts(network, rates, sanity_rates)
        )

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

        :arg provider: A web3 provider
        :arg account: Account to sign transactions.
        :arg str address: The address of smart contract
        """
        super().__init__(provider, account, address, CONVERSION_RATES_CODE.abi)
        self.token_indices = {}
        self.executor = futures.ThreadPoolExecutor(max_workers=4)

    def get_buy_rate(self, token, qty, block_number=0):
        """Return the buying rate (ETH based). The rate might be vary with
        different quantity.

        :arg str token: Token address
        :arg int qty: The amount to buy
        :arg int block_number: The block number to get rate from, default value
            0 means latest block number
        """
        return self.contract.functions.getRate(
            token,
            block_number,
            True,  # buy = True
            qty
        ).call()

    def get_sell_rate(self, token, qty, block_number=0):
        """Return the selling rate (ETH based). The rate might be vary with
        different quantity.

        :arg str token: Token address
        :arg int qty: The amount to sell
        :arg int block_number: The block number to get rate from, default value
            0 means latest block number
        """
        return self.contract.functions.getRate(
            token,
            block_number,
            False,  # buy = False -> sell
            qty
        ).call()

    def get_token_indices(self, token):
        """Get token index in pricing contract compact data.

        :arg str token: The token address

        Returns array index and field index of token in compact data.
        """
        if token not in self.token_indices:
            arr_idx, field_idx, _, _ = self.contract.functions.getCompactData(
                token).call()
            self.token_indices[token] = TokenIndex(arr_idx, field_idx)
        return self.token_indices[token]

    def build_price(self, token, buy, sell):
        """Calculate price data.

        :arg list(str) token: the token address
        :arg list(int) buy: token buy price
        :arg list(int) sell: token sell price

        :return: token, base buy and sell, compact buy and sell, base_changed

            * token: the token address
            * base_buy: the base buy price
            * compact_buy: the different between current base buy and \
                new buy price, in bps unit
            * base_sell: the base sell price
            * compact_sell: the different between current base sell and \
                new sell price, in bps unit
            * base_changed: if compact can not fit in a byte, we need to set \
                new base rate. Otherwise, the compact price will be set

        """
        base_buy = self.get_basic_rate(token, True)
        compact_buy = get_compact_data(buy, base_buy)

        base_sell = self.get_basic_rate(token, False)
        compact_sell = get_compact_data(sell, base_sell)

        base_changed = compact_buy.base_changed or compact_sell.base_changed

        return {
            'token': token,
            'base_buy': compact_buy.base,
            'base_sell': compact_sell.base,
            'compact_buy': compact_buy.compact,
            'compact_sell': compact_sell.compact,
            'base_changed': base_changed
        }

    def set_rates(self, token_addresses, buy_rates, sell_rates):
        """Setting rates for tokens.

        :arg list(str) token_addresses: list of token contract addresses
            supported by your reserve

        :arg list(int) buy_rates: list of buy rates in token wei
            eg: 1 ETH = 500 KNC -> 500 * (10**18)

        :arg list(int) sell_rates: list of sell rates in token wei
            eg: 1 KNC = 0.00182 ETH -> 0.00182 * (10**18)

        """

        token_indices = {}
        for idx, indices in enumerate(self.executor.map(
                self.get_token_indices, token_addresses)):
            token_indices[token_addresses[idx]] = indices

        prices = list(self.executor.map(lambda p: self.build_price(*p), zip(
            token_addresses, buy_rates, sell_rates)))

        tokens = []
        base_buy = []
        base_sell = []
        for price in prices:
            if price['base_changed']:
                tokens.append(price['token'])
                base_buy.append(price['base_buy'])
                base_sell.append(price['base_sell'])

        compact_buy, compact_sell, indices = build_compact_price(
            prices, token_indices)

        if tokens:
            """Set base rate"""
            tx_hash = self.call_contract_func(
                self.contract.functions.setBaseRate(
                    tokens,
                    base_buy,  # base buy
                    base_sell,  # base sell
                    compact_buy,  # compact data
                    compact_sell,  # compact data
                    self.w3.eth.blockNumber,  # most recent block number
                    indices,  # indicies
                )
            )
        else:
            """Set compact rate"""
            tx_hash = self.call_contract_func(
                self.contract.functions.setCompactData(
                    compact_buy,
                    compact_sell,
                    self.w3.eth.blockNumber,
                    indices
                )
            )
        return tx_hash

    def get_basic_rate(self, token_address, buy=True):
        """Get basic rate from pricing contract."""
        return self.contract.functions.getBasicRate(
            token_address, buy).call()

    def enable_token_trade(self, token):
        return self.call_contract_func(
            self.contract.functions.enableTokenTrade(token)
        )

    def disable_token_trade(self, token):
        return self.call_contract_func(
            self.contract.functions.disableTokenTrade(token)
        )

    def add_token(self, token):
        return self.call_contract_func(
            self.contract.functions.addToken(token)
        )

    def set_valid_rate_duration_in_blocks(self, duration):
        return self.call_contract_func(
            self.contract.functions.setValidRateDurationInBlocks(
                duration
            )
        )

    def set_token_control_info(self,
                               token,
                               minimal_record_resolution,
                               max_per_block_imbalance,
                               max_total_imbalance):
        return self.call_contract_func(
            self.contract.functions.setTokenControlInfo(
                token,
                minimal_record_resolution,
                max_per_block_imbalance,
                max_total_imbalance
            )
        )

    def set_qty_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        return self.call_contract_func(
            self.contract.functions.setQtyStepFunction(
                token,
                x_buy,
                y_buy,
                x_sell,
                y_sell
            )
        )

    def set_imbalance_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        return self.call_contract_func(
            self.contract.functions.setImbalanceStepFunction(
                token,
                x_buy,
                y_buy,
                x_sell,
                y_sell
            )
        )

    def set_compact_data(self, buy, sell, indices):
        return self.call_contract_func(
            self.contract.functions.setCompactData(
                buy,
                sell,
                self.w3.eth.blockNumber,
                indices
            )
        )

    def get_compact_data(self, token):
        return self.contract.functions.getCompactData(token).call()

    def set_reserve_address(self, reserve_addr):
        """Update reserve address."""
        return self.call_contract_func(
            self.contract.functions.setReserveAddress(reserve_addr)
        )

    def get_reserve_address(self):
        return self.contract.functions.reserveContract().call()

    def get_step_function_data(self, token, command, param):
        return self.contract.functions.getStepFunctionData(
            token,
            command,
            param
        ).call()

    def add_new_token(self, token, minimal_record_resolution,
                      max_per_block_imbalance, max_total_imbalance):
        """Add new token to pricing contract.

        :arg str token: The token address
        :arg int minimal_record_resolution: Recommended value is the token unit
            equivalent of $0.0001
        :arg int max_per_block_imbalance: The maximum token wei amount of
            net absolute (+/-) change for a token in a block
        :arg int max_total_imbalance: The token amount of the net token change
            that happens between 2 prices updates
        """
        self.add_token(token)
        self.set_token_control_info(
            token, minimal_record_resolution,
            max_per_block_imbalance, max_total_imbalance
        )
        self.enable_token_trade(token)
        self.get_token_indices(token)


class SanityRatesContract(BaseContract):
    """SanityRatesContract represents the KyberNetwork sanity rates contract.
    This contract prevent unusual rates from conversion rates contract to be
    used.
    """

    def __init__(self, provider, account, address):
        """Create new SanityRatesContract instance.

        :arg str provider: web3 provider
        :arg account: the account to sign transaction
        :arg str address: the address of sanity rates contract
        """
        super().__init__(provider, account, address, SANITY_RATES_CODE.abi)

    def set_sanity_rates(self, tokens, rates):
        """Set the sanity rates for a list of tokens.

        :arg list(str) tokens: list of ERC20 token contract address
        :arg list(int) rates: list of rates in ETH wei
        """
        return self.call_contract_func(
            self.contract.functions.setSanityRates(tokens, rates)
        )

    def get_sanity_rates(self, src, dst):
        """Get the sanity rates for 1 token vs. ETH."""
        return self.contract.functions.getSanityRate(src, dst).call()

    def set_reasonable_diff(self, tokens, diff):
        """Set reasonable conversion rate difference in percentage. Any rate
        outside of this range is considered unreasonable.

        :arg list(str) tokens: list of ERC20 token contract address
        :arg list(int) diff: list of reasonable difference in basis points
        """
        return self.call_contract_func(
            self.contract.functions.setReasonableDiff(tokens, diff)
        )

    def get_reasonable_diff_in_bps(self, token):
        """Get the reasonable difference in basis points for token."""
        return self.contract.functions.reasonableDiffInBps(token).call()


class Reserve:
    """Reserve represent a KyberNetwork reserve SDK.

    A wrapper to interact with reserve contracts, including:

        * Reserve operations
        * Get/Set pricing
        * Withdraw funds
        * Enable/Disable trading function
    """

    def __init__(self, provider, account, addresses):
        """Create a Reserve instance.

        :arg provider: web3 provider
        :arg addresses: addresses of deployed smart contracts
        """
        self.fund = ReserveContract(
            provider, account, addresses.reserve)
        self.pricing = ConversionRatesContract(
            provider, account, addresses.conversion_rates)
        self.sanity = SanityRatesContract(
            provider, account, addresses.sanity_rates
        )
