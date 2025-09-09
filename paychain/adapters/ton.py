"""TON adapter using TonAPI REST."""
import os
import requests

from paychain.core.types import TxQuery, TxRecord, TxPage

# Base TonAPI URL. MAY CHANGE.
API_URL = "https://tonapi.io/v2"


def list_transactions(q: TxQuery) -> TxPage:
    """Return last transactions for the given address on TON."""
    base = q.rpc_url or API_URL
    api_key = q.api_key or os.getenv("TONAPI_TOKEN")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    params = {"limit": q.limit, "sort": "desc"}
    resp = requests.get(f"{base}/accounts/{q.address}/events", params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events") or data.get("items") or []
    items: list[TxRecord] = []
    for ev in events:
        ts = ev.get("timestamp") or ev.get("utime")
        if q.since_ts and ts and ts < q.since_ts:
            continue
        if q.until_ts and ts and ts > q.until_ts:
            continue
        actions = ev.get("actions", [])
        for act in actions:
            tt = act.get("type")
            if tt not in ("TonTransfer", "SimpleTransfer"):
                continue
            info = act.get("TonTransfer") or act.get("SimpleTransfer") or act.get("action", {})
            from_addr = info.get("sender") or info.get("from")
            to_addr = info.get("recipient") or info.get("to")
            amount = int(info.get("amount", 0))
            direction = "incoming" if to_addr == q.address else "outgoing" if from_addr == q.address else "all"
            if q.direction == "incoming" and direction != "incoming":
                continue
            if q.direction == "outgoing" and direction != "outgoing":
                continue
            items.append(
                TxRecord(
                    chain="TON",
                    tx_id=str(ev.get("event_id")) if ev.get("event_id") else str(ev.get("lt")),
                    ts=ts,
                    block_height=ev.get("lt"),
                    from_addr=from_addr,
                    to_addr=to_addr,
                    amount_raw=amount,
                    amount_decimals=9,
                    asset="TON",
                    status="confirmed",
                )
            )
            break
        if len(items) >= q.limit:
            break
    return TxPage(items=items)
