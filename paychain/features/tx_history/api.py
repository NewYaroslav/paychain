"""Unified transaction history API."""
from paychain.core.types import TxQuery, TxPage
from paychain.adapters import btc, eth, sol, ton, tron


def list_transactions(chain: str, q: TxQuery) -> TxPage:
    """Dispatch to an adapter based on chain string."""
    chain = chain.upper()
    if chain == "BTC":
        return btc.list_transactions(q)
    if chain == "ETH":
        return eth.list_transactions(q)
    if chain == "SOL":
        return sol.list_transactions(q)
    if chain == "TON":
        return ton.list_transactions(q)
    if chain in ("TRON", "TRX"):
        return tron.list_transactions(q)
    raise ValueError(f"Unsupported chain: {chain}")
