import os
import sys
import eth_tester


"""Modify the path to resolve the reserve_sdk package"""
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

"""By default, the eth_tester set GAS_LIMIT is only 3141592, it's not enough
for the reserve contracts.
"""
eth_tester.backends.pyevm.main.GENESIS_GAS_LIMIT = 10000000
