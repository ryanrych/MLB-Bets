from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

import statsapi


def _flatten_schedule(schedule_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    games: List[Dict[str, Any]] = []
    for day in schedule_json.get("dates", []):
        games.extend(day.get("games", []))
    return games


def _winner_team_id(game: Dict[str, Any]) -> Optional[int]:
    away = game["teams"]["away"]
    home = game["teams"]["home"]

    if away.get("isWinner") is True:
        return away["team"]["id"]
    if home.get("isWinner") is True:
        return home["team"]["id"]

    # Fallback in case isWinner is missing
    away_score = away.get("score")
    home_score = home.get("score")
    if away_score is None or home_score is None:
        return None

    if away_score > home_score:
        return away["team"]["id"]
    if home_score > away_score:
        return home["team"]["id"]
    return None


def find_series_sweep_opportunities(target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return today's games that are:
      1) the last game of the series, and
      2) one team has won every previous game in that series.

    target_date format: YYYY-MM-DD
    """
    if target_date is None:
        target_date = date.today().isoformat()

    today_schedule = statsapi.get(
        "schedule",
        {
            "sportId": 1,
            "date": target_date,
            "hydrate": "seriesStatus",
        },
    )

    today_games = _flatten_schedule(today_schedule)
    results: List[Dict[str, Any]] = []

    for game in today_games:
        series_game_number = game.get("seriesGameNumber")
        games_in_series = game.get("gamesInSeries")

        # Must be the final game of a multi-game series
        if not series_game_number or not games_in_series:
            continue
        if series_game_number != games_in_series or series_game_number <= 1:
            continue

        away_team = game["teams"]["away"]["team"]
        home_team = game["teams"]["home"]["team"]
        current_game_pk = game["gamePk"]
        season = game["season"]
        current_game_dt = datetime.fromisoformat(game["gameDate"].replace("Z", "+00:00"))

        # Pull all season head-to-head games between these two clubs
        head_to_head = statsapi.get(
            "schedule",
            {
                "sportId": 1,
                "teamId": home_team["id"],
                "opponentId": away_team["id"],
                "season": season,
            },
        )

        previous_games = []
        for prior in _flatten_schedule(head_to_head):
            if prior["gamePk"] == current_game_pk:
                continue

            prior_dt = datetime.fromisoformat(prior["gameDate"].replace("Z", "+00:00"))
            if prior_dt >= current_game_dt:
                continue

            # Only count completed prior games
            if prior.get("status", {}).get("abstractGameState") != "Final":
                continue

            previous_games.append(prior)

        previous_games.sort(
            key=lambda g: (
                g["officialDate"],
                g["gameDate"],
                g.get("gameNumber", 1),
                g["gamePk"],
            )
        )

        needed = series_game_number - 1
        series_previous_games = previous_games[-needed:]

        # If we can't confidently identify the previous games in this series, skip it
        if len(series_previous_games) != needed:
            continue

        winners = [_winner_team_id(g) for g in series_previous_games]
        if None in winners:
            continue

        unique_winners = set(winners)
        if len(unique_winners) != 1:
            continue

        leader_id = winners[0]
        if leader_id == away_team["id"]:
            leader_name = away_team["name"]
            trailer_name = home_team["name"]
        else:
            leader_name = home_team["name"]
            trailer_name = away_team["name"]

        results.append(
            {
                "gamePk": current_game_pk,
                "gameDate": game["gameDate"],
                "officialDate": game["officialDate"],
                "awayTeam": away_team["name"],
                "homeTeam": home_team["name"],
                "gamesInSeries": games_in_series,
                "seriesGameNumber": series_game_number,
                "teamWithSweepChance": leader_name,
                "teamFacingSweep": trailer_name,
                "seriesRecordSoFar": f"{leader_name} leads {needed}-0",
                "seriesStatus": game.get("seriesStatus", {}).get("result"),
            }
        )

    return results


if __name__ == "__main__":
    games = find_series_sweep_opportunities("2026-03-29")

    if not games:
        print("No sweep-opportunity games found today.")
    else:
        print("Today's sweep-opportunity games:")
        for g in games:
            print(g)
