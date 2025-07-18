"""
Module: aml.external.chainabuse
Description: 
"""

import httpx
from core.config import config
from loguru import logger

CHAINABUSE_API_URL = "https://api.chainabuse.com/api/v1/reports/address/"

async def fetch_chainabuse_reports(address: str, network: str = "tron") -> list:
    if not config.enable_chainabuse:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{CHAINABUSE_API_URL}{network}/{address}",
                headers={
                    "X-API-Key": config.chainabuse_api_key,
                    "User-Agent": "paychain-aml-checker"
                }
            )
            r.raise_for_status()
            data = r.json()
            return data.get("reports", [])
    except Exception as e:
        logger.warning(f"Chainabuse fetch failed: {e}")
        return []