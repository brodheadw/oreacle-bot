# src/client.py
from dataclasses import dataclass, asdict
from enum import Enum
import os, time, requests

API = "https://api.manifold.markets/v0"
HDRS = lambda key: {"Authorization": f"Key {key}", "Content-Type": "application/json"}

class Outcome(str, Enum):
    YES = "YES"
    NO  = "NO"

@dataclass
class LimitOrder:
    contractId: str
    outcome: Outcome           # Outcome.YES / Outcome.NO
    amount: int                # M$ integer
    limitProb: float           # 0.0–1.0
    expiresMillisAfter: int = 6*60*60*1000  # optional

    def validate(self):
        assert self.amount > 0
        assert 0.0 <= self.limitProb <= 1.0

    def payload(self):
        self.validate()
        d = asdict(self)
        d["outcome"] = self.outcome.value   # Enum → "YES"/"NO"
        return d

@dataclass
class Comment:
    contractId: str
    markdown: str

class ManifoldClient:
    def __init__(self, api_key: str, base_url: str = API, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries

    def _post(self, path: str, json: dict):
        for i in range(self.max_retries):
            r = requests.post(f"{self.base_url}{path}", headers=HDRS(self.api_key), json=json, timeout=20)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()  # last one
        return r.json()

    def get_market_by_slug(self, slug: str):
        r = requests.get(f"{self.base_url}/slug/{slug}", timeout=20)
        r.raise_for_status()
        return r.json()

    # Generic limit order
    def place_limit(self, order: LimitOrder):
        return self._post("/bet", order.payload())

    # Convenience wrappers
    def place_limit_yes(self, contract_id: str, amount: int, limit_prob: float):
        return self.place_limit(LimitOrder(contract_id, Outcome.YES, amount, limit_prob))

    def place_limit_no(self, contract_id: str, amount: int, limit_prob: float):
        return self.place_limit(LimitOrder(contract_id, Outcome.NO, amount, limit_prob))

    def post_comment(self, c: Comment):
        return self._post("/comment", asdict(c))