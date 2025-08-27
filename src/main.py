import os, requests

API = "https://api.manifold.markets/v0"
KEY = os.environ["MANIFOLD_API_KEY"]
SLUG = os.environ["MARKET_SLUG"]
HDRS = {"Authorization": f"Key {KEY}", "Content-Type": "application/json"}

def get_market_by_slug(slug: str):
    r = requests.get(f"{API}/slug/{slug}", headers=HDRS)
    r.raise_for_status()
    return r.json()

def post_comment(contract_id: str, markdown: str):
    r = requests.post(f"{API}/comments", headers=HDRS, json={
        "contractId": contract_id,
        "text": markdown,
    })
    r.raise_for_status()
    return r.json()

def place_limit_yes(contract_id: str, amount: int, limit_prob: float):
    r = requests.post(f"{API}/bet", headers=HDRS, json={
        "contractId": contract_id,
        "amount": amount,
        "outcome": "YES",
        "limitProb": limit_prob,            # e.g., 0.47 = 47%
        "expiresMillisAfter": 6*60*60*1000, # 6 hrs
    })

def place_limit_no(contract_id: str, amount: int, limit_prob: float):


if __name__ == "__main__":
    mkt = get_market_by_slug(SLUG)
    cid = mkt["id"]
    # 1) Say hello (costs M$1)
    # post_comment(cid, "**Oreacle online.** (hello world test)")
    place_limit_yes(cid, amount=1, limit_prob=0.7)
    print("Placed limit YES bet of M$1 at 70%")