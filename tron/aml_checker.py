"""
Module: tron.aml_checker
Description: Asynchronous TRON AML checker with modular heuristics.
"""

import time
import httpx
from loguru import logger
from core.config import config
from aml.aml_cache import MdbxAmlCache
from aml.tron_config import aml_config
from aml.external.chainabuse import check_address_chainabuse

TRONSCAN_API = "https://apilist.tronscanapi.com/api"
TRON_NETWORK = "tron"
aml_cache = MdbxAmlCache()


# === Запросы ===

async def fetch_account_info(address: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{TRONSCAN_API}/account?address={address}",
            headers={"User-Agent": "paychain-aml-checker"}
        )
        r.raise_for_status()
        return r.json()
        
async def fetch_trc20_transfers(address: str, limit=100) -> list:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{TRONSCAN_API}/token_trc20/transfers",
            params={"toAddress": address, "limit": limit, "sort": "-timestamp"},
            headers={"User-Agent": "paychain-aml-checker"}
        )
        r.raise_for_status()
        return r.json().get("token_transfers", [])

# === Aml Контекст ===

@dataclass
class AmlContext:
    def __init__(self, network: str, address: str):
        self.network = network
        self.address = address
        self.account_info: dict = {}
        self.trc20_transfers: list = []
        self.chainabuse_reports: list = []

    async def preload(self):
        self.account_info = await fetch_account_info(self.address)
        self.trc20_transfers = await fetch_trc20_transfers(self.address)
        self.chainabuse_reports = await fetch_chainabuse_reports(self.address, "tron")
        
# === Эвристики ===

async def check_high_tx_volume(ctx: AmlContext):
    cfg = aml_config["high_tx_volume"]
    if ctx.account_info.get("totalTransactionCount", 0) > cfg["threshold"]:
        return "high_tx_volume", cfg["weight"]

async def check_large_balance(ctx: AmlContext):
    cfg = aml_config["large_balance"]
    if float(ctx.account_info.get("balance", 0)) > cfg["threshold"]:
        return "large_balance", cfg["weight"]

async def check_new_account(ctx: AmlContext):
    cfg = aml_config["newly_created"]
    create_time = ctx.account_info.get("createTime", 0)
    if create_time > 0:
        age_ms = time.time() * 1000 - create_time
        if age_ms < cfg["max_age_ms"]:
            return "newly_created", cfg["weight"]

async def check_dust_activity(ctx: AmlContext):
    cfg = aml_config["dust_activity"]
    count = sum(1 for t in ctx.trc20_transfers if int(t.get("amount", "0")) < cfg["dust_limit"])
    if count >= cfg["min_count"]:
        return "dust_activity", cfg["weight"]

async def check_many_senders(ctx: AmlContext):
    cfg = aml_config["many_unique_senders"]
    senders = {t["from_address"] for t in ctx.trc20_transfers if "from_address" in t}
    if len(senders) > cfg["min_count"]:
        return "many_unique_senders", cfg["weight"]

async def check_tx_burst_activity(ctx: AmlContext):
    cfg = aml_config["tx_burst_activity"]
    tx_count = ctx.account_info.get("totalTransactionCount", 0)
    create_ts = ctx.account_info.get("createTime", 0)
    if create_ts > 0:
        age_days = (time.time() * 1000 - create_ts) / (1000 * 60 * 60 * 24)
        if age_days < cfg["max_age_days"] and tx_count > cfg["min_tx"]:
            return "tx_burst_activity", cfg["weight"]
            
async def check_address_chainabuse(ctx) -> tuple | None:
    cfg = aml_config["chainabuse"]
    if not cfg.get("enabled", False):
        return None

    allowed_categories = set(cfg.get("categories", []))
    max_age_days = cfg.get("max_age_days", 30)
    weight = cfg.get("weight", 0.25)

    reports = await fetch_chainabuse_reports(ctx.address, ctx.network)
    ctx.chainabuse_reports = reports  # сохраняем в контекст

    if not reports:
        return None

    now = datetime.utcnow()
    min_time = now - timedelta(days=max_age_days)

    for r in reports:
        cat = r.get("category", "")
        ts = r.get("created_at") or r.get("createdAt")
        if not cat or cat not in allowed_categories or not ts:
            continue

        try:
            report_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if report_time >= min_time:
                return "chainabuse_reported", weight
        except Exception:
            continue

    return None
    
async def check_senders_aml(
    ctx: AmlContext, 
    shared_sender_cache: 
    dict[str, dict], 
    current_depth: int = 0
) -> tuple[str, float] | None:
    conf = aml_config["check_senders_aml"]
    if not conf["enabled"]:
        return None
        
    if current_depth >= conf["max_depth"]:
        return None

    transfers = ctx.trc20_transfers[:conf["max_incoming"]]
    senders = list({t["from_address"] for t in transfers if "from_address" in t})
    
    suspicious = 0
    checked = 0

    for addr in senders:
        if addr in shared_sender_cache:
            result = shared_sender_cache[addr]
        else:
            if current_depth >= conf["max_depth"]:
                continue
            result = await check_address(
                addr, 
                force_refresh=False, 
                context=shared_sender_cache, 
                current_depth=current_depth + 1
            )
            shared_sender_cache[addr] = result

        if result["status"] in ("blocked", "warning"):
            suspicious += 1

        checked += 1
        if checked >= conf["max_senders_checked"]:
            break

    if suspicious >= conf["min_suspicious_senders"]:
        return "senders_with_risk", conf["weight"]
        
    return None

# === Основная проверка ===

async def check_address(address: str, force_refresh=False, context: Optional[dict] = None, current_depth: int = 0) -> dict:
    """
    Asynchronously check a TRON address using AML heuristics and weighted scoring.

    :param address: TRON base58 address
    :param force_refresh: Ignore cached results
    :return: AML result
    """
    context = context or {}
    
    if address in context:
        return context[address]

    # Проверка блоклиста
    if config.is_blocked_address(address):
        return {"status": "blocked", "score": 1.0, "flags": ["blocked_locally"]}

    # Кэш
    if not force_refresh and not aml_cache.is_expired(TRON_NETWORK, address):
        cached = aml_cache.get(TRON_NETWORK, address)
        if cached:
            return cached

    try:
        ctx = AmlContext(TRON_NETWORK, address)
        await ctx.preload()

        flags = []
        score = 0.0
        sender_cache = context

        checks = [
            check_high_tx_volume,
            check_large_balance,
            check_new_account,
            check_tx_burst_activity,
            check_dust_activity,
            check_many_senders,
            check_address_chainabuse,
            lambda ctx: check_senders_aml(ctx, sender_cache, current_depth),
        ]

        for check in checks:
            result = await check(ctx)
            if result:
                flag, weight = result
                flags.append(flag)
                score += weight

        score = round(min(score, 1.0), 3)

        if "blocked_locally" in flags:
            status = "blocked"
        elif score >= 0.7:
            status = "blocked"
        elif score >= 0.3:
            status = "warning"
        else:
            status = "safe"

        result = {
            "status": status,
            "score": score,
            "flags": flags,
            "source": "auto",
            "checked_at": int(time.time())
        }

        aml_cache.set(TRON_NETWORK, address, result)
        context[address] = result
        return result

    except Exception as e:
        logger.exception("AML check failed:")
        return {
            "status": "error",
            "score": 1.0,
            "flags": ["aml_check_error", str(e)],
            "source": "error",
            "checked_at": int(time.time())
        }