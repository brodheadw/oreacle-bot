# src/main.py
from client import ManifoldClient, Comment
import os

KEY = os.environ["MANIFOLD_API_KEY"]
SLUG = os.environ["MARKET_SLUG"]

if __name__ == "__main__":
    cli = ManifoldClient(KEY)
    mkt = cli.get_market_by_slug(SLUG)
    cid = mkt["id"]

    # place NO limit at 53%
    cli.place_limit_no(contract_id=cid, amount=5, limit_prob=0.53)

    # quick comment
    cli.post_comment(Comment(contractId=cid, markdown="Oreacle placed a NO limit at 53%."))