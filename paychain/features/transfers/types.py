"""Basic transfer types."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TransferRequest:
    from_addr: str
    to_addr: str
    amount_raw: int
    fee: Optional[int] = None
