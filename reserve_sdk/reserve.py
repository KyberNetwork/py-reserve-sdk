from .contracts import (
    ReserveContract, ConversionRatesContract, SanityRatesContract
)


class Reserve:
    """Reserve is a wrapper to call methods in order to manage a reserve.
    Including:

        * Control permission
        * Manage fund
        * Pricing
    """

    def __init__(self, provider, account, addresses):
        """Create a Reserve instance.

        :arg provider: web3 provider
        :arg addresses: addresses of deployed smart contracts
        """
        self.fund = ReserveContract(provider, account, addresses.reserve)
        self.pricing = ConversionRatesContract(
            provider, account, addresses.conversion_rates)
        self.sanity = SanityRatesContract(
            provider, account, addresses.sanity_rates
        )

    def change_account(self, account):
        """Change the account to sign transactions."""
        self.fund.change_account(account)
        self.pricing.change_account(account)
        self.sanity.change_account(account)

    def link_contracts(self, network, reserve, pricing, sanity):
        """Link reserve contracts.

        * Set fund contract address for pricing contract.
        * Set network contract, pricing contract and sanity contract addresses\
        for fund contract.

        :arg str network: the Kyber network contract address
        :arg str reserve: the reserve contract address
        :arg str pricing: the pricing contract address
        :arg str sanity: the sanity contract address

        """
        self.pricing.set_reserve_address(reserve)
        self.fund.set_contracts(network, pricing, sanity)

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
        self.pricing.add_token(token)
        self.pricing.set_token_control_info(
            token, minimal_record_resolution,
            max_per_block_imbalance, max_total_imbalance
        )
        self.pricing.enable_token_trade(token)
        self.pricing.get_token_indices(token)

    def get_balance(self, token):
        """Return balance of given token.

        :arg str token: Token address
        :return: The balance of token
        """
        return self.fund.get_balance(token)

    def approve_withdraw_address(self, address, token):
        """Allow given address to withdraw a specific token from reserve.

        :arg str address: Address to allow withdrawal
        :arg str token: Token address
        """
        return self.fund.approve_withdraw_address(address, token)

    def disapprove_withdraw_address(self, address, token):
        """Disallow an address to withdraw a specific token from reserve.

        :arg str address: Address to disallow withdrawal
        :arg str token: Token address
        """
        return self.fund.disapprove_withdraw_address(address, token)

    def approved_withdraw_address(self, address, token):
        """Check if withdraw token from reserve to given address is approved.
        """
        return self.fund.approved_withdraw_addresses(address, token)

    def withdraw(self, token, amount, dest):
        """Withdraw token from reserve to destination address.

        :arg str token: Token address
        :arg int amount: Amount of token to withdraw
        :arg str dest: Destination address to receive the token
        """
        self.fund.withdraw(token, amount, dest)

    def enable_trade(self):
        """Enable trading function for reserve contract."""
        self.fund.enable_trade()

    def disable_trade(self):
        """Disable trading function for reserve contract."""
        self.fund.disable_trade()

    def trade_enabled(self):
        """Get trading function status."""
        return self.fund.trade_enabled()

    def get_buy_rate(self, token, qty, block_number=0):
        """Return the buying rate (ETH based). The rate might be vary with
        different quantity.

        :arg str token: Token address
        :arg int qty: The amount to buy
        :arg int block_number: The block number to get rate from, default value
            0 means latest block number
        """
        return self.pricing.get_buy_rate(token, qty, block_number)

    def get_sell_rate(self, token, qty, block_number=0):
        """Return the selling rate (ETH based). The rate might be vary with
        different quantity.

        :arg str token: Token address
        :arg int qty: The amount to buy
        :arg int block_number: The block number to get rate from, default value
            0 means latest block number
        """
        return self.pricing.get_sell_rate(token, qty, block_number)

    def set_rates(self, token_addresses, buy_rates, sell_rates):
        """Setting rates for tokens.

        :arg list(str) token_addresses: list of token contract addresses
            supported by your reserve

        :arg list(int) buy_rates: list of buy rates in token wei
            eg: 1 ETH = 500 KNC -> 500 * (10**18)

        :arg list(int) sell_rates: list of sell rates in token wei
            eg: 1 KNC = 0.00182 ETH -> 0.00182 * (10**18)

        """
        return self.pricing.set_rates(token_addresses, buy_rates, sell_rates)

    def set_qty_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        """Set adjustment to alter pricing depend on the size of \
        buy/sell order.

        :arg str token: The token address
        :arg list(int) x_buy: The buy steps in token wei
        :arg list(int) y_buy: The impact on buy rate in basis point
        :arg list(int) x_sell: The sell steps in token wei
        :arg list(int) y_sell: The impact on sell rate in basis point

        :return: The transaction hash
        """
        return self.pricing.set_qty_step_function(
            token, x_buy, y_buy, x_sell, y_sell)

    def set_imbalance_step_function(self, token, x_buy, y_buy, x_sell, y_sell):
        """Set adjustment to alter pricing depend on the net traded amount.

        :arg str token: The token address
        :arg list(int) x_buy: The buy steps in token wei
        :arg list(int) y_buy: The impact on buy rate in basis point
        :arg list(int) x_sell: The sell steps in token wei
        :arg list(int) y_sell: The impact on sell rate in basis point

        :return: The transaction hash
        """
        return self.pricing.set_imbalance_step_function(
            token, x_buy, y_buy, x_sell, y_sell)

    def get_steps_function_data(self, token, command, param):
        """Get steps function data from contract."""
        return self.pricing.get_steps_function_data(
            token, command, param)

    def set_valid_rate_duration_in_blocks(self, duration):
        """Set the duration for rates to be expired, in block unit.

        :arg int duration: the time in blocks that conversion rates will \
        expire since the last price update.
        """
        return self.pricing.set_valid_rate_duration_in_blocks(duration)

    def set_sanity_rates(self, tokens, rates):
        """Set the sanity rates for a list of tokens.

        :arg list(str) tokens: list of ERC20 token contract address
        :arg list(int) rates: list of rates in ETH wei
        """
        return self.sanity.set_sanity_rates(tokens, rates)

    def get_sanity_rates(self, src, dst):
        """Get the sanity rates for 1 token vs. ETH."""
        return self.sanity.get_sanity_rates(src, dst)

    def set_reasonable_diff(self, tokens, diff):
        """Set reasonable conversion rate difference in percentage. Any rate
        outside of this range is considered unreasonable.

        :arg list(str) tokens: list of ERC20 token contract address
        :arg list(int) diff: list of reasonable difference in basis points
        """
        return self.sanity.set_reasonable_diff(tokens, diff)

    def get_reasonable_diff_in_bps(self, token):
        """Get the reasonable difference in basis points for token."""
        return self.sanity.get_reasonable_diff_in_bps(token)
