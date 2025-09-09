import os
import time
import pytest

from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions
import requests

# Popular SOL address. Source: https://solscan.io/account/4NDtcSzsMMgPMhm7VM5GJ9N2MvmFoXxSg6uSPRqGQ2S9 (Binance)
DEFAULT_SOL_ADDR = "4NDtcSzsMMgPMhm7VM5GJ9N2MvmFoXxSg6uSPRqGQ2S9"


def _addr() -> str:
    addr = os.getenv("SOL_ADDR", DEFAULT_SOL_ADDR)
    if not addr:
        pytest.skip("env not set")
    return addr


def test_sol_smoke():
    addr = _addr()
    rpc = os.getenv("SOL_RPC_URL")
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        page = list_transactions("SOL", TxQuery(address=addr, rpc_url=rpc, since_ts=week_ago, limit=5))
    except requests.HTTPError:
        pytest.skip("api error")
    if not page.items:
        pytest.skip("no transactions")
    tx = page.items[0]
    assert tx.tx_id
    assert tx.amount_decimals in {9, 0}
    assert tx.asset in {"SOL", "TOKEN"}
    assert tx.status in {"confirmed", "pending", "failed", "unknown"}
