from collections import namedtuple

from web3 import Web3

from .contract_code import (
    RESERVE_CODE, CONVERSION_RATES_CODE, SANITY_RATES_CODE)
from .utils import send_transaction, hexlify


"""Show token position in the compact data."""
TokenIndex = namedtuple('TokenIndex', ('array_idx', 'field_idx'))
CompactData = namedtuple('CompactData', ('base', 'compact'))


def get_compact_data(rate, base):
    """
    Calculate compact data from new rate and base rate.

    Args:
        rate: value of new sell/buy price
        base: value of current sell/buy price at contract

    Returns:
        compact_data which include new base rate & compact value which is the
        different between rate and base in bps unit.

    TODO consider to raise BaseChangedException to indicates that base rates
    were changed, in this situation, we can only set base rates, not compact
    data.
    """
    if base == 0:
        return CompactData(rate, 0)

    compact = int((rate/base - 1) * 1000)
    if compact <= -128 or compact >= 127:  # not fit in a byte
        return CompactData(rate, 0)
    else:
        # handle negative value to convert to byte
        if compact < 0:
            compact += 256
        return CompactData(base, compact)


def build_compact_price(prices, token_indices):
    """Prepare compact price to setCompactData through pricing contract.

    Args:
        prices: price change in bps unit
        token_indices: index of token in compact data on contract

    Return:
        buy: buy prices change in bps unit, encoded in hex
        sell: sell prices change in bps unit, encoded in hex
        indices: the index of block token in compact data on contract

    TODO improve function documentation with example.
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

        Args:
            address: new admin address

        Returns transaction hash.
        """
        tx = self.contract.functions.transferAdmin(address).buildTransaction()
        return self.send_transaction(tx)

    def claim_admin(self):
        """Claim admin privilege.
        The account address should be in already placed in pendingAdmin for
        this to works.
        Returns transaction hash.
        """
        tx = self.contract.functions.claimAdmin().buildTransaction()
        return self.send_transaction(tx)

    def add_operator(self, address):
        """Add given address to operators list.

        Args:
            address: new operator address

        Returns transaction hash.
        """
        tx = self.contract.functions.addOperator(address).buildTransaction()
        return self.send_transaction(tx)

    def remove_operator(self, address):
        """Remove given address from operators list.

        Args:
            address: operator address

        Returns transaction hash.
        """
        tx = self.contract.functions.removeOperator(address).buildTransaction()
        return self.send_transaction(tx)

    def add_alerter(self, address):
        """Add given address to alerters list.

        Args:
            address: new alerter address

        Returns transaction hash.
        """
        tx = self.contract.functions.addAlerter(address).buildTransaction()
        return self.send_transaction(tx)

    def remove_alerter(self, address):
        """Remove given address from alerters list.

        Args:
            address: alerter address

        Returns transaction hash.
        """
        tx = self.contract.functions.removeAlerter(address).buildTransaction()
        return self.send_transaction(tx)

    def change_account(self, account):
        """TODO: need to review this behaviour. Client could init an other
        instance of contract with new account.
        """
        self.account = account
        self.w3.eth.defaultAccount = account.address

    def send_transaction(self, tx):
        """Send a transaction using instance w3, account.

        Args:
            tx: transaction data

        Return transaction hash.
        """
        return send_transaction(self.w3, self.account, tx)


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
        """
        sha = Web3.soliditySha3(['address', 'address'], [token, address])
        return self.contract.functions.approvedWithdrawAddresses(sha).call()

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
        tx = self.contract.functions.enableTrade().buildTransaction()
        return self.send_transaction(tx)

    def disable_trade(self):
        """Disable trading feature for reserve contract."""
        tx = self.contract.functions.disableTrade().buildTransaction()
        return self.send_transaction(tx)

    def approve_withdraw_address(self, address, token):
        """Allow given address to withdraw a specific token from reserve.

        Args:
            address: address to allow withdrawal
            token: token address
        """
        tx = self.contract.functions.approveWithdrawAddress(
            token, address, True
        ).buildTransaction()
        return self.send_transaction(tx)

    def disapprove_withdraw_address(self, address, token):
        """Disallow an address to withdraw a specific token from reserve.

        Args:
            address: address to disallow withdrawal
            token: token address
        """
        tx = self.contract.functions.approveWithdrawAddress(
            token, address, False
        ).buildTransaction()
        return self.send_transaction(tx)

    def withdraw(self, token, amount, dest):
        """Withdraw token from reserve to destination address.

        Args:
            token: token address
            amount: amount of token to withdraw
            dest: destination address to receive the token
        """
        tx = self.contract.functions.withdraw(
            token, amount, dest).buildTransaction({
                'gas': 3000000
            })
        return self.send_transaction(tx)

    def set_contracts(self, network, rates, sanity_rates):
        """Update relevant address to reserve.

        Args:
            network: the address of KyberNetwork
            rates: the address of conversions rates contract
            sanity_rates: the address of sanity rates contract
        """
        tx = self.contract.functions.setContracts(
            network, rates, sanity_rates).buildTransaction()
        return self.send_transaction(tx)

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
        self.token_indices = {}

    def get_buy_rate(self, token, qty):
        """Return the buying rate (ETH based). The rate might be vary with
        different quantity.

        Args:
            token: token address
            qty: the amount to buy
        """
        return self.contract.functions.getRate(
            token,
            self.w3.eth.blockNumber,  # most recent block
            True,  # buy = True
            qty
        ).call()

    def get_sell_rate(self, token, qty):
        """Return the selling rate (ETH based). The rate might be vary with
        different quantity.

        Args:
            token: token address
            qty: the amount of token to sell
        """
        return self.contract.functions.getRate(
            token,
            self.w3.eth.blockNumber,  # most recent block
            False,  # buy = False -> sell
            qty
        ).call()

    def get_token_indices(self, token):
        """Get token index in pricing contract compact data.

        Args:
            token: the token address

        Returns array index and field index of token in compact data.
        """
        if token not in self.token_indices:
            arr_idx, field_idx, _, _ = self.contract.functions.getCompactData(
                token).call()
            self.token_indices[token] = TokenIndex(arr_idx, field_idx)
        return self.token_indices[token]

    def build_price(self, token, buy, sell):
        """Calculate price data.

        Args:
            token: the token address
            buy: token buy price
            sell: token sell price

        Returns:
            token: the token address # TODO consider to remove this output
            compact_buy: the different between current current base buy and new
            buy price, in bps unit
            compact_sell: the different between current current base sell and
            new sell price, in bps unit
            base_changed: this value is True if compact cant fit in a byte, in
            that situation, need to set new base rate. Otherwise, the compact
            price will be set.
        """
        base_buy = self.get_basic_rate(token, True)
        compact_buy = get_compact_data(buy, base_buy)

        base_sell = self.get_basic_rate(token, False)
        compact_sell = get_compact_data(sell, base_sell)

        base_changed = (compact_buy.base != base_buy) or (
            compact_sell.base != base_sell)

        return {
            'token': token,
            'compact_buy': compact_buy.compact,
            'compact_sell': compact_sell.compact,
            'base_changed': base_changed
        }

    def set_rates(self, token_addresses, buy_rates, sell_rates):
        """Setting rates for tokens.

        Args:
            token_addresses: list of token contract addresses supported by your
            reserve

            buy_rates: list of buy rates in token wei
                eg: 1 ETH = 500 KNC -> 500 * (10**18)

            sell_rates: list of sell rates in token wei
                eg: 1 KNC = 0.00182 ETH -> 0.00182 * (10**18)

        Steps:
            get token_indices
            build prices

            if base_change:
                set new base_rate
            else
                set compact_data

            base_change if
            - no base_change exist
            - compact data not fit in a byte, out of range -128...127 bps

        TODO improve performance to get token_indices and prices concurrently.
        """

        # loop = asyncio.get_event_loop()

        # token_indices = loop.run_until_complete(asyncio.gather(
        #     *[self.get_token_indices(token) for token in token_addresses]
        # ))

        # prices = loop.run_until_complete(asyncio.gather(
        #     *[self.build_price(token, buy, sell) for token, buy, sell in
        #       zip(token_addresses, buy_rates, sell_rates)]
        # ))

        # loop.close()

        token_indices = {
            token: self.get_token_indices(token) for token in token_addresses
        }

        prices = [
            self.build_price(token, buy, sell) for token, buy, sell in
            zip(token_addresses, buy_rates, sell_rates)
        ]

        base_changed = any([p['base_changed'] for p in prices])

        if base_changed:
            """Set base rate"""
            tx = self.contract.functions.setBaseRate(
                token_addresses,
                buy_rates,  # base buy
                sell_rates,  # base sell
                [],  # compact data
                [],  # compact data
                self.w3.eth.blockNumber,  # most recent block number
                [],  # indicies
            ).buildTransaction()
        else:
            """Set compact rate"""
            buy, sell, indices = build_compact_price(prices, token_indices)
            tx = self.contract.functions.setCompactData(
                buy,
                sell,
                self.w3.eth.blockNumber,
                indices
            ).buildTransaction()
        return self.send_transaction(tx)

    def get_basic_rate(self, token_address, buy=True):
        """Get basic rate from pricing contract."""
        return self.contract.functions.getBasicRate(
            token_address, buy).call()

    def enable_token_trade(self, token):
        tx = self.contract.functions.enableTokenTrade(token).buildTransaction()
        return self.send_transaction(tx)

    def disable_token_trade(self, token):
        tx = self.contract.functions.disableTokenTrade(
            token).buildTransaction()
        return self.send_transaction(tx)

    def add_token(self, token):
        tx = self.contract.functions.addToken(token).buildTransaction()
        return self.send_transaction(tx)

    def set_valid_rate_duration_in_blocks(self, duration):
        tx = self.contract.functions.setValidRateDurationInBlocks(
            duration
        ).buildTransaction()
        return self.send_transaction(tx)

    def set_token_control_info(self,
                               token,
                               minimal_record_resolution,
                               max_per_block_imbalance,
                               max_total_imbalance):

        tx = self.contract.functions.setTokenControlInfo(
            token,
            minimal_record_resolution,
            max_per_block_imbalance,
            max_total_imbalance
        ).buildTransaction()
        return self.send_transaction(tx)

    def set_qty_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        tx = self.contract.functions.setQtyStepFunction(
            token,
            x_buy,
            y_buy,
            x_sell,
            y_sell
        ).buildTransaction({'gas': 5000000})
        return self.send_transaction(tx)

    def set_imbalance_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        tx = self.contract.functions.setImbalanceStepFunction(
            token,
            x_buy,
            y_buy,
            x_sell,
            y_sell
        ).buildTransaction({'gas': 5000000})
        return self.send_transaction(tx)

    def set_compact_data(self, buy, sell, indices):
        tx = self.contract.functions.setCompactData(
            buy,
            sell,
            self.w3.eth.blockNumber,
            indices
        ).buildTransaction({'gas': 5000000})
        return self.send_transaction(tx)

    def get_compact_data(self, token):
        return self.contract.functions.getCompactData(token).call()

    def set_reserve_address(self, reserve_addr):
        """Update reserve address."""
        tx = self.contract.functions.setReserveAddress(
            reserve_addr).buildTransaction()
        return self.send_transaction(tx)

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

        Args:
            token: the token address.
            minimal_record_resolution: recommended value is the token unit
            equivalent of $0.0001
            max_per_block_imbalance: the maximum token wei amount of
            net absolute (+/-) change for a token in a block
            max_total_imbalance: the token amount of the net token change that
            happens between 2 prices updates

        Steps:
            1. Add token address to pricing contract.
            2. Set token control info .
            3. Enable token trade.
        """
        self.add_token(token)
        self.set_token_control_info(
            token, minimal_record_resolution,
            max_per_block_imbalance, max_total_imbalance
        )
        self.enable_token_trade(token)


class SanityRatesContract(BaseContract):
    """SanityRatesContract represents the KyberNetwork sanity rates contract.
    This contract prevent unusual rates from conversion rates contract to be
    used.
    """

    def __init__(self, provider, account, address):
        """Create new SanityRatesContract instance."""
        super().__init__(provider, account, address, SANITY_RATES_CODE.abi)

    def set_sanity_rates(self, tokens, rates):
        """Set the sanity rates for a list of tokens.

        Args:
            tokens: list of ERC20 token contract address
            rates: list of rates in ETH wei

        E.g:
            1 KNC = 0.002 ETH = 2000000000000000 wei
        """
        tx = self.contract.functions.setSanityRates(
            tokens, rates
        ).buildTransaction({'gas': 5000000})
        return self.send_transaction(tx)

    def get_sanity_rates(self, src, dst):
        """Get the sanity rates for 1 token vs. ETH."""
        return self.contract.functions.getSanityRate(src, dst).call()

    def set_reasonable_diff(self, tokens, diff):
        """Set reasonable conversion rate difference in percentage. Any rate
        outside of this range is considered unreasonable.

        Args:
            tokens: list of ERC20 token contract address
            diff: list of reasonable difference in basis points (1bps = 0.01%)

        """
        tx = self.contract.functions.setReasonableDiff(
            tokens, diff
        ).buildTransaction()
        return self.send_transaction(tx)

    def get_reasonable_diff_in_bps(self, token):
        """Get the reasonable difference in basis points for token."""
        return self.contract.functions.reasonableDiffInBps(token).call()


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
        self.fund = ReserveContract(
            provider, account, addresses.reserve)
        self.pricing = ConversionRatesContract(
            provider, account, addresses.conversion_rates)
        self.sanity = SanityRatesContract(
            provider, account, addresses.sanity_rates
        )
