from datetime import datetime

from mlb import find_series_sweep_opportunities
from kalshi import fetch_all_open_markets


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
# markets = fetch_all_open_markets()
for game in games:
    print(convert_name_to_kalshi(game["teamFacingSweep"]))


