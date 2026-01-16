# src/ingestion/rss_ingestor.py

import json
import os
from datetime import datetime
from typing import List

import feedparser

from src.ingestion.signal import Signal


SEEN_IDS_FILE = "seen_ids.json"


def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return set(json.load(f))


def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def ingest_rss_feed(feed_url: str, domain: str, subdomain: str) -> List[Signal]:
    feed = feedparser.parse(feed_url)
    seen_ids = load_seen_ids()

    new_signals = []

    for entry in feed.entries:
        item_id = f"{feed_url}::{entry.get('id') or entry.get('link')}"
        if not item_id or item_id in seen_ids:
            continue

        seen_ids.add(item_id)

        text = f"{entry.get('title', '')}. {entry.get('summary', '')}"

        signal = Signal(
            signal_id=item_id,
            text=text.strip(),
            timestamp=datetime.utcnow(),
            source=feed_url,
            domain=domain,
            subdomain=subdomain,
            metadata={}
        )

        new_signals.append(signal)

    save_seen_ids(seen_ids)
    return new_signals