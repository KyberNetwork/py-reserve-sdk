from .utils import send_transaction


class Token():

    def __init__(self, address, abi, w3, account):
        self.address = address
        self.__w3 = w3
        self.__contract = w3.eth.contract(address=address, abi=abi)
        self.__account = account

    def balanceOf(self, address):
        return self.__contract.functions.balanceOf(address).call()

    def transfer(self, address, amount):
        tx = self.__contract.functions.transfer(
            address, amount).buildTransaction()
        return send_transaction(self.__w3, self.__account, tx)
