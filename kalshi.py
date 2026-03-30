import requests

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


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

    return all_markets


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
    mlb_moneylines = [m for m in markets if is_mlb_moneyline_market(m)]

    print(f"Found {len(mlb_moneylines)} MLB moneyline markets\n")

    for m in mlb_moneylines:
        print(f"Ticker:       {m.get('ticker')}")
        print(f"Event Ticker: {m.get('event_ticker')}")
        print(f"Title:        {m.get('title')}")
        print(f"Status:       {m.get('status')}")
        print(f"Yes Bid:      {m.get('yes_bid_dollars')}")
        print(f"Yes Ask:      {m.get('yes_ask_dollars')}")
        print(f"Volume:       {m.get('volume_fp')}")
        print(f"Close Time:   {m.get('close_time')}")
        print("-" * 60)


if __name__ == "__main__":
    main()
