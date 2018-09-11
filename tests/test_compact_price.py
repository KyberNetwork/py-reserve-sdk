import random

from reserve_sdk.contracts import get_compact_data, build_compact_price
from reserve_sdk.contracts import TokenIndex, CompactData
from reserve_sdk.utils import hexlify


def test_compact_data_with_small_change_in_rates():
    base_rate = 500 * 10**18
    changes = random.randint(-128, 127)  # this value can fit in a byte
    new_rate = int(base_rate * (1 + changes / 1000))

    compact = get_compact_data(new_rate, base_rate)

    assert compact.base == base_rate
    if changes >= 0:
        assert abs(compact.compact - changes) <= 1
    else:
        assert abs(compact.compact - (changes + 256)) <= 1
    assert not compact.base_changed


def test_compact_data_with_big_change_in_rates():
    base_rate = 0.0018200 * 10**18
    changes = 200  # this value can not fit in a byte
    new_rate = int(base_rate * (1 + changes / 1000))

    assert get_compact_data(
        new_rate, base_rate) == CompactData(new_rate, 0, True)


def test_compact_data_with_zero_base_rates():
    assert get_compact_data(100, 0) == CompactData(100, 0, True)
    assert get_compact_data(0, 0) == CompactData(0, 0, False)


def check_list_equal(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


def test_build_compact_price():
    addr_1 = '0x14535eE720e329f66071B86486763Da4637034aE'
    addr_2 = '0x24535eE720e329f66071B86486763Da4637034aE'
    addr_3 = '0x34535eE720e329f66071B86486763Da4637034aE'

    prices = [
        {
            'token': addr_1,
            'compact_buy': 23,
            'compact_sell': 26
        },
        {
            'token': addr_2,
            'compact_buy': 24,
            'compact_sell': 27
        },
        {
            'token': addr_3,
            'compact_buy': 25,
            'compact_sell': 28
        }
    ]

    token_indices = {
        addr_1: TokenIndex(3, 9),
        addr_2: TokenIndex(9, 5),
        addr_3: TokenIndex(9, 6)
    }

    compact_buy, compact_sell, indices = build_compact_price(
        prices, token_indices)

    assert check_list_equal(indices, [3, 9])

    assert check_list_equal(compact_buy, [
        hexlify([0, 0, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 0]),
        hexlify([0, 0, 0, 0, 0, 24, 25, 0, 0, 0, 0, 0, 0, 0])
    ])

    assert check_list_equal(compact_sell, [
        hexlify([0, 0, 0, 0, 0, 0, 0, 0, 0, 26, 0, 0, 0, 0]),
        hexlify([0, 0, 0, 0, 0, 27, 28, 0, 0, 0, 0, 0, 0, 0])
    ])
