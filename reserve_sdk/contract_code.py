import os
import json
from collections import namedtuple

# Container of smart contract code.
ContractCode = namedtuple('ContractCode', ('abi', 'bin'))

__contract_code_file_path = os.path.join(os.path.dirname(__file__),
                                         'reserve_contracts_code.json')
with open(__contract_code_file_path) as f:
    contract_codes = json.load(f)

RESERVE_CODE = ContractCode(
    contract_codes['reserve']['abi'],
    contract_codes['reserve']['bytecode']
)
CONVERSION_RATES_CODE = ContractCode(
    contract_codes['conversion_rates']['abi'],
    contract_codes['conversion_rates']['bytecode']
)
SANITY_RATES_CODE = ContractCode(
    contract_codes['sanity_rates']['abi'],
    contract_codes['sanity_rates']['bytecode'],
)
