"""TRON adapter fetching TRC-20 transfers from TronGrid."""
import os
import requests

from paychain.core.types import TxQuery, TxRecord, TxPage

# Base TronGrid API. MAY CHANGE.
API_URL = "https://api.trongrid.io"
# Default USDT TRC-20 contract. MAY CHANGE.
USDT_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"


def list_transactions(q: TxQuery) -> TxPage:
    """Return last TRC-20 transactions for the given address (default USDT)."""
    base = q.rpc_url or API_URL
    contract = q.token or os.getenv("TRON_USDT_CONTRACT") or USDT_CONTRACT
    api_key = q.api_key or os.getenv("TRON_API_KEY")
    headers = {"Accept": "application/json"}
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key
    params = {
        "event_name": "Transfer",
        "to": q.address,
        "only_to": "true",
        "limit": q.limit,
    }
    if q.since_ts:
        params["min_block_timestamp"] = int(q.since_ts) * 1000
    url = f"{base}/v1/contracts/{contract}/events"
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("data", [])
    items: list[TxRecord] = []
    for ev in events:
        result = ev.get("result", {})
        ts = ev.get("block_timestamp")
        if q.until_ts and ts and ts/1000 > q.until_ts:
            continue
        from_addr = result.get("from")
        to_addr = result.get("to")
        amount = int(result.get("value", 0))
        direction = "incoming"
        if q.direction == "outgoing" and from_addr != q.address:
            continue
        items.append(
            TxRecord(
                chain="TRON",
                tx_id=ev.get("transaction_id"),
                ts=int(ts/1000) if ts else None,
                block_height=ev.get("block_number"),
                from_addr=from_addr,
                to_addr=to_addr,
                amount_raw=amount,
                amount_decimals=int(result.get("decimal", 6)),
                asset="USDT",
                status="confirmed",
            )
        )
        if len(items) >= q.limit:
            break
    return TxPage(items=items)
