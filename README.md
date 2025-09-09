# PayChain

Lightweight toolkit with portable modules for fetching transaction history
from popular blockchains. Each adapter is a single file that depends only on
`requests` and exposes a unified API.

## Structure

```
paychain/
  core/                # shared types
  adapters/            # chain specific modules (BTC/ETH/SOL/TON/TRON)
  features/
    tx_history/        # simple dispatcher over adapters
    aml/               # placeholder
    transfers/         # placeholder
  examples/            # CLI utilities
  tests/               # smoke tests
```

## Usage

```python
from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions

page = list_transactions("ETH", TxQuery(
    address="0x....",
    api_key="YOUR_ETHERSCAN_KEY",
    limit=10,
))
for tx in page.items:
    print(tx.tx_id, tx.amount_raw, tx.asset, tx.status)
```

### CLI

```
python -m paychain.examples.tx_list_recent --chain ETH --address 0x... --api-key $ETHERSCAN_API_KEY --limit 5 --json
```

## Tests

Set environment variables for the desired chains:
`BTC_ADDR`, `ETH_ADDR`, `ETHERSCAN_API_KEY`, `SOL_ADDR`, `SOL_RPC_URL`,
`TON_ADDR`, `TONAPI_TOKEN`, `TRON_ADDR`, `TRON_API_KEY`, `TRON_USDT_CONTRACT`.
Then run:

```
pytest -q
```

Public RPC/REST endpoints and schemas **may change**.
