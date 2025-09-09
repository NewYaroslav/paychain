"""Ethereum adapter using Etherscan-compatible REST API."""
import os

import requests

from paychain.core.types import TxQuery, TxRecord, TxPage

# Default Etherscan API URL. MAY CHANGE.
API_URL = "https://api.etherscan.io/api"


def list_transactions(q: TxQuery) -> TxPage:
    """Return last transactions for the given address on Ethereum."""
    api_url = q.rpc_url or API_URL
    api_key = q.api_key or os.getenv("ETHERSCAN_API_KEY")
    params = {
        "module": "account",
        "address": q.address,
        "sort": "desc",
        "page": 1,
        "offset": q.limit,
    }
    if q.token:
        params["action"] = "tokentx"
        params["contractaddress"] = q.token
    else:
        params["action"] = "txlist"
    if q.since_ts:
        params["starttimestamp"] = q.since_ts
    if q.until_ts:
        params["endtimestamp"] = q.until_ts
    if api_key:
        params["apikey"] = api_key
    resp = requests.get(api_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    txs = data.get("result", [])
    if isinstance(txs, str):
        txs = []
    items: list[TxRecord] = []
    for tx in txs:
        ts = int(tx.get("timeStamp")) if tx.get("timeStamp") else None
        if q.since_ts and ts and ts < q.since_ts:
            continue
        if q.until_ts and ts and ts > q.until_ts:
            continue
        from_addr = tx.get("from")
        to_addr = tx.get("to")
        direction = "unknown"
        addr_l = q.address.lower()
        if from_addr and from_addr.lower() == addr_l:
            direction = "outgoing"
        if to_addr and to_addr.lower() == addr_l:
            direction = "incoming"
        if q.direction == "incoming" and direction != "incoming":
            continue
        if q.direction == "outgoing" and direction != "outgoing":
            continue
        asset = "ETH"
        decimals = 18
        amount = int(tx.get("value", 0))
        if q.token:
            asset = tx.get("tokenSymbol") or "TOKEN"
            decimals = int(tx.get("tokenDecimal")) if tx.get("tokenDecimal") else 0
        status = "failed" if tx.get("isError") == "1" else "confirmed"
        items.append(
            TxRecord(
                chain="ETH",
                tx_id=tx.get("hash"),
                ts=ts,
                block_height=int(tx.get("blockNumber")) if tx.get("blockNumber") else None,
                from_addr=from_addr,
                to_addr=to_addr,
                amount_raw=amount,
                amount_decimals=decimals,
                asset=asset,
                status=status,
            )
        )
        if len(items) >= q.limit:
            break
    return TxPage(items=items)
