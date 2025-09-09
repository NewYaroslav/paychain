"""Solana adapter using JSON-RPC requests."""
import requests
from typing import List

from paychain.core.types import TxQuery, TxRecord, TxPage

# Default Solana RPC URL. MAY CHANGE.
RPC_URL = "https://api.mainnet-beta.solana.com"


def _rpc_call(url: str, method: str, params: List) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("result")


def list_transactions(q: TxQuery) -> TxPage:
    """Return last transactions for the given address on Solana."""
    url = q.rpc_url or RPC_URL
    limit = q.limit
    sig_params = [q.address, {"limit": limit}]
    signatures = _rpc_call(url, "getSignaturesForAddress", sig_params) or []
    items: list[TxRecord] = []
    for sig_info in signatures:
        sig = sig_info.get("signature")
        ts = sig_info.get("blockTime")
        if q.since_ts and ts and ts < q.since_ts:
            continue
        if q.until_ts and ts and ts > q.until_ts:
            continue
        tx = _rpc_call(
            url,
            "getTransaction",
            [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}],
        )
        if not tx:
            continue
        meta = tx.get("meta", {})
        status = "failed" if meta.get("err") else "confirmed"
        block_time = tx.get("blockTime")
        slot = tx.get("slot")
        added = False
        if not q.token:
            message = tx.get("transaction", {}).get("message", {})
            instructions = message.get("instructions", [])
            for inst in instructions:
                if inst.get("program") == "system" and inst.get("parsed", {}).get("type") == "transfer":
                    info = inst["parsed"]["info"]
                    from_addr = info.get("source")
                    to_addr = info.get("destination")
                    amount = int(info.get("lamports", 0))
                    direction = "incoming" if to_addr == q.address else "outgoing" if from_addr == q.address else "all"
                    if q.direction == "incoming" and direction != "incoming":
                        break
                    if q.direction == "outgoing" and direction != "outgoing":
                        break
                    items.append(
                        TxRecord(
                            chain="SOL",
                            tx_id=sig,
                            ts=block_time,
                            block_height=slot,
                            from_addr=from_addr,
                            to_addr=to_addr,
                            amount_raw=amount,
                            amount_decimals=9,
                            asset="SOL",
                            status=status,
                        )
                    )
                    added = True
                    break
        else:
            mint = q.token
            pre = meta.get("preTokenBalances", [])
            post = meta.get("postTokenBalances", [])
            pre_amt = 0
            post_amt = 0
            decimals = 0
            for b in pre:
                if b.get("owner") == q.address and b.get("mint") == mint:
                    pre_amt = int(b.get("uiTokenAmount", {}).get("amount", 0))
                    decimals = int(b.get("uiTokenAmount", {}).get("decimals", 0))
            for b in post:
                if b.get("owner") == q.address and b.get("mint") == mint:
                    post_amt = int(b.get("uiTokenAmount", {}).get("amount", 0))
                    decimals = int(b.get("uiTokenAmount", {}).get("decimals", decimals))
            delta = post_amt - pre_amt
            if delta != 0:
                direction = "incoming" if delta > 0 else "outgoing"
                if q.direction == "incoming" and direction != "incoming":
                    pass
                elif q.direction == "outgoing" and direction != "outgoing":
                    pass
                else:
                    items.append(
                        TxRecord(
                            chain="SOL",
                            tx_id=sig,
                            ts=block_time,
                            block_height=slot,
                            from_addr=None,
                            to_addr=None,
                            amount_raw=abs(delta),
                            amount_decimals=decimals,
                            asset="TOKEN",
                            status=status,
                        )
                    )
                    added = True
        if added and len(items) >= q.limit:
            break
    return TxPage(items=items)
