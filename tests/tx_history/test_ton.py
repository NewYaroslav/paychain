import os
import time
import pytest

from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions
import requests

# Default TON address disabled to avoid API errors. Set TON_ADDR env to run.
DEFAULT_TON_ADDR = None


def _addr() -> str:
    addr = os.getenv("TON_ADDR", DEFAULT_TON_ADDR)
    if not addr:
        pytest.skip("env not set")
    return addr


def test_ton_smoke():
    addr = _addr()
    api_key = os.getenv("TONAPI_TOKEN")
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        page = list_transactions("TON", TxQuery(address=addr, api_key=api_key, since_ts=week_ago, limit=5))
    except requests.HTTPError:
        pytest.skip("api error")
    if not page.items:
        pytest.skip("no transactions")
    tx = page.items[0]
    assert tx.tx_id
    assert tx.amount_decimals == 9
    assert tx.asset == "TON"
    assert tx.status in {"confirmed", "pending", "failed", "unknown"}
