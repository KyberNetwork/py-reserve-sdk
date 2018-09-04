from .utils import call_contract


class Token():

    def __init__(self, address, abi, w3, account):
        self.address = address
        self.__w3 = w3
        self.__contract = w3.eth.contract(address=address, abi=abi)
        self.__account = account

    def balanceOf(self, address):
        return self.__contract.functions.balanceOf(address).call()

    def transfer(self, address, amount):
        func = self.__contract.functions.transfer(
            address, amount)
        return call_contract(self.__w3, self.__account, func)
