import os
import time
import pytest

from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions
import requests

# Popular ETH address. Source: https://etherscan.io/address/0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740 (Binance)
DEFAULT_ETH_ADDR = "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740"


def _addr() -> str:
    addr = os.getenv("ETH_ADDR", DEFAULT_ETH_ADDR)
    if not addr:
        pytest.skip("env not set")
    return addr


def test_eth_smoke():
    addr = _addr()
    api_key = os.getenv("ETHERSCAN_API_KEY")
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        page = list_transactions("ETH", TxQuery(address=addr, api_key=api_key, since_ts=week_ago, limit=5))
    except requests.HTTPError:
        pytest.skip("api error")
    if not page.items:
        pytest.skip("no transactions")
    tx = page.items[0]
    assert tx.tx_id
    assert tx.amount_decimals in {18, 0}
    assert tx.asset in {"ETH", "TOKEN"}
    assert tx.status in {"confirmed", "pending", "failed", "unknown"}
