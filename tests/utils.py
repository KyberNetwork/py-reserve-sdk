import json
import os


from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3, EthereumTesterProvider

from reserve_sdk import Deployer, Reserve
from reserve_sdk.utils import deploy_contract, token_wei
from reserve_sdk.contract_code import ContractCode
from reserve_sdk.token import Token

NETWORK_ADDR = '0x91a502C678605fbCe581eae053319747482276b9'

backend = PyEVMBackend()
tester = EthereumTester(backend)
provider = EthereumTesterProvider(tester)
w3 = Web3(provider)

test_accounts = []
for key in backend.account_keys:
    test_accounts.append(w3.eth.account.privateKeyToAccount(key.to_hex()))

# deploy test tokens
token_code_file_path = os.path.join(os.path.dirname(__file__),
                                    'erc20_token_code.json')

with open(token_code_file_path) as f:
    token_code = json.load(f)
    erc20_token_code = ContractCode(
        abi=token_code['abi'], bin=token_code['bytecode'])

tokens = []
for i in range(3):
    token_addr = deploy_contract(
        w3,
        test_accounts[0],
        erc20_token_code,
        [str(i), str(i), 18]
    )

    token = Token(token_addr, erc20_token_code.abi, w3, test_accounts[0])
    tokens.append(token)
