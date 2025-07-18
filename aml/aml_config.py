"""
Module: aml.tron_config
Description: Configurable thresholds and weights for AML heuristics.
"""

tron_config = {
    "high_tx_volume": {
        "threshold": 5000,
        "weight": 0.2
    },
    "large_balance": {
        "threshold": 1_000_000_000,  # in SUN
        "weight": 0.2
    },
    "newly_created": {
        "max_age_ms": 86_400_000,  # 1 day
        "weight": 0.15
    },
    "dust_activity": {
        "dust_limit": 100_000,      # < 0.1 USDT
        "min_count": 10,
        "weight": 0.15
    },
    "many_unique_senders": {
        "min_count": 20,
        "weight": 0.2
    },
    "tx_burst_activity": {
        "min_tx": 100,
        "max_age_days": 3,
        "weight": 0.15
    },
    "chainabuse": {
        "enabled": True,
        "categories": ["Scam", "Rug Pull", "Phishing"],  # допустимые категории
        "max_age_days": 30,  # не старше
        "weight": 0.25,
    },
	"check_senders_aml": {
		"enabled": True,
		"max_incoming": 50,
		"max_senders_checked": 10,
		"min_suspicious_senders": 2,
		"max_depth": 2,
		"weight": 0.25,
	},
}
