import binascii


def call_contract(w3, account, func):
    """Send transaction to execute smart contract function.

    Args:
        w3: web3 instance
        account: local account
        func: the smart contract function

    Returns transaction hash.
    """
    tx = func.buildTransaction({
        'nonce': w3.eth.getTransactionCount(account.address),
        'gas': func.estimateGas()
    })
    signed_tx = w3.eth.account.signTransaction(tx, account.privateKey)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return tx_hash


def get_transaction_receipt(w3, tx_hash, timeout=180):
    return w3.eth.waitForTransactionReceipt(tx_hash, timeout)


def deploy_contract(w3, account, contract_code, contract_args):
    """Deploy a single smart contract
        Args:
            abi: contract's abi
            bytecode: contract's bytecode
            contract_args: arguments to construct the contract
        Returns: the deployed smart contract address
    """
    contract = w3.eth.contract(
        abi=contract_code.abi,
        bytecode=contract_code.bin
    )
    func = contract.constructor(*contract_args)
    tx_hash = call_contract(w3, account, func)
    tx_receipt = get_transaction_receipt(w3, tx_hash)
    return tx_receipt['contractAddress']


def hexlify(arr):
    return '0x{}'.format(binascii.hexlify(bytearray(arr)).decode())


def token_wei(value, decimals):
    return int(value * 10**decimals)
