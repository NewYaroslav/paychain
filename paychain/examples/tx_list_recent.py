"""CLI example to print recent transactions for any supported chain."""
import argparse
import json
from paychain.core.types import TxQuery
from paychain.features.tx_history.api import list_transactions


def main() -> None:
    parser = argparse.ArgumentParser(description="List recent transactions")
    parser.add_argument("--chain", required=True)
    parser.add_argument("--address", required=True)
    parser.add_argument("--since", type=int, default=None)
    parser.add_argument("--until", type=int, default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--rpc-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--token", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    q = TxQuery(
        address=args.address,
        since_ts=args.since,
        until_ts=args.until,
        limit=args.limit,
        rpc_url=args.rpc_url,
        api_key=args.api_key,
        token=args.token,
    )
    page = list_transactions(args.chain, q)
    if args.json:
        print(json.dumps([tx.__dict__ for tx in page.items], indent=2))
    else:
        for tx in page.items:
            print(tx)


if __name__ == "__main__":
    main()
