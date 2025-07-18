"""
Module: core.config
Description: Centralized storage and access to paychain global parameters.
"""

import os
from core.env_loader import load_env

load_env()  # Load .env before accessing any environment variables

class PaychainConfig:
    def __init__(self):
        # Master seed for address generation
        self.mnemonic = os.getenv("SEED_MNEMONIC", "").strip()
        self.salt = os.getenv("TRON_SALT", "").strip()
        self.master_address_tron = os.getenv("TRON_MASTER_ADDRESS", "").strip()

        # Chainabuse
        self.chainabuse_api_key = os.getenv("CHAINABUSE_API_KEY", "").strip()
        self.enable_chainabuse = bool(self.chainabuse_api_key)

        # Local in-memory blocklists
        self._blocklist_addr = set()
        self._blocklist_uid = set()

    # === Зерно ===
    def get_seed(self) -> str:
        return self.mnemonic

    def get_salt(self) -> str:
        return self.salt

    # === Блоклисты ===
    def is_blocked_address(self, addr: str) -> bool:
        return addr in self._blocklist_addr

    def is_blocked_user(self, user_id: int) -> bool:
        return user_id in self._blocklist_uid

    def add_blocked_address(self, addr: str):
        self._blocklist_addr.add(addr)

    def remove_blocked_address(self, addr: str):
        self._blocklist_addr.discard(addr)

    def add_blocked_user(self, user_id: int):
        self._blocklist_uid.add(user_id)

    def remove_blocked_user(self, user_id: int):
        self._blocklist_uid.discard(user_id)

    def list_blocked_addresses(self):
        return list(self._blocklist_addr)

    def list_blocked_users(self):
        return list(self._blocklist_uid)

config = PaychainConfig()
