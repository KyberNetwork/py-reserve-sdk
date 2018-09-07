class Addresses:
    """A container of all reserve contracts address.

    * reserve: the address of fund contract
    * conversion_rates: the address of pricing contract
    * sanity_rates: the address of sanity contract
    """

    def __init__(self, reserve, conversion_rates, sanity_rates):
        """Create an addresses instance."""
        self.reserve = reserve
        self.conversion_rates = conversion_rates
        self.sanity_rates = sanity_rates
