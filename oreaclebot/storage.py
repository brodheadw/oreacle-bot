# src/storage.py
from __future__ import annotations
import sqlite3, os, time
from dataclasses import dataclass

DB_PATH = os.environ.get("OREACLE_DB", "./tmp/oreacle.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
source TEXT NOT NULL,
item_id TEXT NOT NULL,
url TEXT,
title TEXT,
ts INTEGER,
PRIMARY KEY (source, item_id)
);
"""

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute(SCHEMA)
    return con

@dataclass
class SeenItem:
    source: str
    item_id: str
    url: str
    title: str
    ts: int

class Store:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.con = _conn()

    def has(self, source: str, item_id: str) -> bool:
        cur = self.con.execute("SELECT 1 FROM seen WHERE source=? AND item_id=?", (source, item_id))
        return cur.fetchone() is not None

    def add(self, item: SeenItem):
        self.con.execute(
        "INSERT OR IGNORE INTO seen(source,item_id,url,title,ts) VALUES(?,?,?,?,?)",
        (item.source, item.item_id, item.url, item.title, item.ts)
        )
        self.con.commit()
    