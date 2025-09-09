"""Bitcoin adapter using Blockstream REST API.
This implementation has no internal dependencies and relies only on requests.
"""
from typing import Optional

import requests

from paychain.core.types import TxQuery, TxRecord, TxPage

# Base URL for Blockstream API. MAY CHANGE.
API_URL = "https://blockstream.info/api"


def _fetch_txs(address: str, last_txid: Optional[str] = None):
    """Fetch a page of transactions for the address."""
    path = f"/address/{address}/txs"
    if last_txid:
        path += f"/chain/{last_txid}"
    resp = requests.get(API_URL + path, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_transactions(q: TxQuery) -> TxPage:
    """Return last transactions for the given address on Bitcoin."""
    addr = q.address
    items: list[TxRecord] = []
    cursor: Optional[str] = None
    remaining = q.limit
    last_txid: Optional[str] = q.extra.get("cursor") if q.extra else None
    while remaining > 0:
        data = _fetch_txs(addr, last_txid)
        if not data:
            break
        for tx in data:
            ts = tx.get("status", {}).get("block_time")
            if q.since_ts and ts and ts < q.since_ts:
                continue
            if q.until_ts and ts and ts > q.until_ts:
                continue
            vin = tx.get("vin", [])
            vout = tx.get("vout", [])
            incoming = any(
                o.get("scriptpubkey_address") == addr for o in vout
            )
            outgoing = any(
                i.get("prevout", {}).get("scriptpubkey_address") == addr for i in vin
            )
            if q.direction == "incoming" and not incoming:
                continue
            if q.direction == "outgoing" and not outgoing:
                continue
            amount = 0
            if incoming:
                for o in vout:
                    if o.get("scriptpubkey_address") == addr:
                        amount += int(o.get("value", 0))
            elif outgoing:
                for i in vin:
                    prev = i.get("prevout", {})
                    if prev.get("scriptpubkey_address") == addr:
                        amount += int(prev.get("value", 0))
            from_addr = vin[0].get("prevout", {}).get("scriptpubkey_address") if vin else None
            to_addr = None
            for o in vout:
                if o.get("scriptpubkey_address") != addr:
                    to_addr = o.get("scriptpubkey_address")
                    break
            status = "confirmed" if tx.get("status", {}).get("confirmed") else "pending"
            items.append(
                TxRecord(
                    chain="BTC",
                    tx_id=tx.get("txid"),
                    ts=ts,
                    block_height=tx.get("status", {}).get("block_height"),
                    from_addr=from_addr,
                    to_addr=to_addr if incoming or outgoing else None,
                    amount_raw=amount if amount else None,
                    amount_decimals=8,
                    asset="BTC",
                    status=status,
                )
            )
            remaining -= 1
            if remaining == 0:
                break
        if len(data) < 25 or remaining == 0:
            break
        last_txid = data[-1]["txid"]
        cursor = last_txid
    return TxPage(items=items, next_cursor=cursor)
