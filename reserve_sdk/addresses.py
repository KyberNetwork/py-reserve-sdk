class Addresses:
    """Addresses contains addresses of all contracts of a KyberNetwork reserve.
    """

    def __init__(self, reserve, conversion_rates, sanity_rates):
        """Create an addresses instance.
        Args:
            reserve: the address of reserve smart contract
            conversionRates: the address of pricing smart contract
            sanityRates: the address of sanity pricing smart contract
        """
        self.reserve = reserve
        self.conversion_rates = conversion_rates
        self.sanity_rates = sanity_rates
