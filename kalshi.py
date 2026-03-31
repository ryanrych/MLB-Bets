import os
import uuid
import base64
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def is_today(iso_time: str) -> bool:
    dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    return dt.date() == datetime.now(timezone.utc).date()


def fetch_all_open_markets():
    all_markets = []
    cursor = None

    while True:
        params = {
            "status": "open",   # not "active"
            "limit": 1000,
        }
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(f"{BASE_URL}/markets", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        markets = data.get("markets", [])
        all_markets.extend(markets)

        cursor = data.get("cursor")
        if not cursor:
            break

    return [m for m in all_markets if is_mlb_moneyline_market(m)]


def is_mlb_moneyline_market(market):
    event_ticker = market.get("event_ticker", "")
    ticker = market.get("ticker", "")

    # MLB game winner markets in your payload use KXMLBGAME
    if not event_ticker.startswith("KXMLBGAME-"):
        return False
    if not ticker.startswith("KXMLBGAME-"):
        return False

    # direct side market, e.g. KXMLBGAME-26MAR301610MINKC-KC
    parts = ticker.split("-")
    if len(parts) != 3:
        return False

    side = parts[-1]
    return 2 <= len(side) <= 4


def main():
    markets = fetch_all_open_markets()

    print(f"Found {len(markets)} MLB moneyline markets\n")

    for m in markets:
        print(m)


def create_signature(private_key, timestamp, method, path):
    message = f"{timestamp}{method}{path}".encode("utf-8")

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode("utf-8")


def buy(private_key, api_key_id, path, data, base_url=BASE_URL):
    """Make an authenticated POST request to the Kalshi API."""
    timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    signature = create_signature(private_key, timestamp, "POST", path)

    headers = {
        'KALSHI-ACCESS-KEY': api_key_id,
        'KALSHI-ACCESS-SIGNATURE': signature,
        'KALSHI-ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }

    return requests.post(base_url + path, headers=headers, json=data)


def load_private_key(path):
    with open(path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None  # change if your key has a password
        )
    return private_key


if __name__ == "__main__":
    main()
