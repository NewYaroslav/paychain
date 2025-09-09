import os
import time
import pytest

from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions
import requests

# Popular TRON address. Source: https://tronscan.org/#/address/TX9K6GTPJbQcVUohMNHFT8MNdwaj3i1nNs (Binance)
DEFAULT_TRON_ADDR = "TX9K6GTPJbQcVUohMNHFT8MNdwaj3i1nNs"


def _addr() -> str:
    addr = os.getenv("TRON_ADDR", DEFAULT_TRON_ADDR)
    if not addr:
        pytest.skip("env not set")
    return addr


def test_tron_smoke():
    addr = _addr()
    api_key = os.getenv("TRON_API_KEY")
    contract = os.getenv("TRON_USDT_CONTRACT")
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        page = list_transactions(
            "TRON",
            TxQuery(address=addr, api_key=api_key, token=contract, since_ts=week_ago, limit=5),
        )
    except requests.HTTPError:
        pytest.skip("api error")
    if not page.items:
        pytest.skip("no transactions")
    tx = page.items[0]
    assert tx.tx_id
    assert tx.amount_decimals == 6
    assert tx.asset == "USDT"
    assert tx.status in {"confirmed", "pending", "failed", "unknown"}
