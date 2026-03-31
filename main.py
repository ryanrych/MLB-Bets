import os
import uuid
from datetime import datetime

from dotenv import load_dotenv

from mlb import find_series_sweep_opportunities
from kalshi import fetch_all_open_markets, buy, load_private_key


load_dotenv()
api_key = os.getenv("API_KEY")
private_key = load_private_key("Jameson1.pem")


def convert_name_to_kalshi(team):

    tokenized = team.split()

    if team == "New York Mets":
        return "New York M"
    elif team == "New York Yankees":
        return "New York Y"
    elif team == "Chicago White Sox":
        return "Chicago W"
    elif team == "Chicago Cubs":
        return "Chicago C"
    elif team == "Los Angeles Dodgers":
        return "Los Angeles D"
    elif team == "Los Angeles Angels":
        return "Los Angeles A"
    elif team == "Athletics":
        return "A's"
    elif len(tokenized) == 3:
        return f"{tokenized[0]} {tokenized[1]}"
    else:
        return tokenized[0]


games = find_series_sweep_opportunities("2026-03-29")
print("games loaded")
markets = fetch_all_open_markets()
print("markets loaded")
for game in games:
    kalshi_name = convert_name_to_kalshi(game["teamFacingSweep"])

    for market in markets:
        if market.get("yes_sub_title") == kalshi_name:

            print("MATCH FOUND")
            print(f"Game: {game['awayTeam']} @ {game['homeTeam']}")
            print(f"Sweep team: {game['teamWithSweepChance']}")
            print(f"Market: {market['ticker']}")
            print(f"YES ask: {market['yes_ask_dollars']}")

            # --- PLACE BET (SAFE PLACEHOLDER) ---
            order = {
                "ticker": market["ticker"],
                "side": "yes",  # or "nojnh" depending on your strategy
                "price": market["yes_ask_dollars"],
                "size": 1,  # number of contracts
            }

            print("Would place order:", order)

            print("\nPlacing order...")
            client_order_id = str(uuid.uuid4())
            order_data = {
                "ticker": market['ticker'],
                "action": "buy",
                "side": "yes",
                "count": 1,
                "type": "limit",
                "yes_price": 10,
                "client_order_id": client_order_id
            }

            response = buy(private_key, api_key, '/portfolio/orders', order_data)

            if response.status_code == 201:
                order = response.json()['order']
                print(f"Order placed successfully!")
                print(f"Order ID: {order['order_id']}")
                print(f"Client Order ID: {client_order_id}")
                print(f"Status: {order['status']}")
                exit()
            else:
                print(f"Error: {response.status_code} - {response.text}")
