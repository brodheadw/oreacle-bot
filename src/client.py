# src/client.py
from dataclasses import dataclass, asdict
from enum import Enum
import os, time, requests

API = "https://api.manifold.markets/v0"
HDRS = {"Authorization": f"Key {KEY}", "Content-Type": "application/json"}

@dataclass
class Outcome(str, Enum):
    YES = "YES"
    NO = "NO"

@dataclass
class LimitOrder:
    contractId: str
    outcome: Outcome
    amount: int
    limitProb: float
    