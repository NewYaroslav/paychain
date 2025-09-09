import os
import time
import pytest

from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions
import requests

# Popular BTC address. Source: https://mempool.space/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT
# May have old transactions only.
DEFAULT_BTC_ADDR = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def _addr() -> str:
    addr = os.getenv("BTC_ADDR", DEFAULT_BTC_ADDR)
    if not addr:
        pytest.skip("env not set")
    return addr


def test_btc_smoke():
    addr = _addr()
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        page = list_transactions("BTC", TxQuery(address=addr, since_ts=week_ago, limit=5))
    except requests.HTTPError:
        pytest.skip("api error")
    if not page.items:
        pytest.skip("no transactions")
    tx = page.items[0]
    assert tx.tx_id
    assert tx.asset == "BTC"
    assert tx.amount_decimals == 8
    assert tx.status in {"confirmed", "pending", "failed", "unknown"}
