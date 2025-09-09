# Comments in English.
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class TxQuery:
    address: str
    since_ts: Optional[int] = None     # UNIX seconds (inclusive)
    until_ts: Optional[int] = None     # UNIX seconds (inclusive)
    limit: int = 50
    direction: str = "all"             # "incoming" | "outgoing" | "all"
    rpc_url: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None        # ERC-20 / Jetton / TRC-20 contract/mint
    extra: Optional[Dict[str, Any]] = None  # chain-specific knobs


@dataclass
class TxRecord:
    chain: str                   # "BTC" | "ETH" | "SOL" | "TON" | "TRON"
    tx_id: str
    ts: Optional[int]            # UNIX seconds if available
    block_height: Optional[int]
    from_addr: Optional[str]
    to_addr: Optional[str]
    amount_raw: Optional[int]    # minimal units (sats/wei/lamports/nanoTON/USDT_6)
    amount_decimals: Optional[int]
    asset: str                   # "BTC" | "ETH" | "SOL" | "TON" | "USDT" | "TOKEN"
    status: str                  # "confirmed" | "pending" | "failed" | "unknown"
    meta: Optional[Dict[str, Any]] = None


@dataclass
class TxPage:
    items: List[TxRecord]
    next_cursor: Optional[str] = None
