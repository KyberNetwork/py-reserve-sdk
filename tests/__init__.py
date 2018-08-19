import os
import sys

"""Modify the path to resolve the reserve_sdk package"""
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
