"""
Module: aml.aml_cache
Description: 
"""

import json
import time
from typing import Optional
import mdbx


class AmlCache:
    def get(self, network: str, address: str) -> Optional[dict]:
        raise NotImplementedError

    def set(self, network: str, address: str, data: dict) -> None:
        raise NotImplementedError

    def delete(self, network: str, address: str) -> None:
        raise NotImplementedError

    def is_expired(self, network: str, address: str, ttl_seconds: int = 86400) -> bool:
        raise NotImplementedError

    def mark_manual_block(self, network: str, address: str) -> None:
        raise NotImplementedError


class MdbxAmlCache(AmlCache):
    def __init__(self, db_path: str = "data/aml_cache.mdbx"):
        self.env = mdbx.Environment(
            db_path,
            geometry=(1 << 20, 1 << 30, 1 << 30),
            max_dbs=1,
            mode=0o644,
        )
        self.db = self.env.open_db(b"aml_cache")

    def _make_key(self, network: str, address: str) -> bytes:
        return f"{network}:{address}".encode()

    def get(self, network: str, address: str) -> Optional[dict]:
        key = self._make_key(network, address)
        with self.env.begin(db=self.db) as txn:
            raw = txn.get(key)
            return json.loads(raw) if raw else None

    def set(self, network: str, address: str, data: dict) -> None:
        key = self._make_key(network, address)
        data.setdefault("checked_at", int(time.time()))
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(key, json.dumps(data).encode())

    def delete(self, network: str, address: str) -> None:
        key = self._make_key(network, address)
        with self.env.begin(write=True, db=self.db) as txn:
            txn.delete(key)

    def is_expired(self, network: str, address: str, ttl_seconds: int = 86400) -> bool:
        record = self.get(network, address)
        if not record:
            return True
        return (time.time() - record.get("checked_at", 0)) > ttl_seconds

    def mark_manual_block(self, network: str, address: str) -> None:
        record = self.get(network, address) or {}
        record.update({
            "status": "blocked",
            "score": 1.0,
            "flags": list(set(record.get("flags", [])) | {"manual_block"}),
            "source": "manual",
            "checked_at": int(time.time()),
        })
        self.set(network, address, record)