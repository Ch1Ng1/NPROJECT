from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "cache" / "predictions_cache.json"
API_URL = "https://v3.football.api-sports.io/fixtures"
DEFAULT_HOME_ELO = 1500
DEFAULT_AWAY_ELO = 1500
DEFAULT_FORM = "DDDDD"
DEFAULT_EXPECTED_GOALS = 2.5
DEFAULT_OVER_25 = 50.0
DEFAULT_YELLOW = 3.6
DEFAULT_CORNERS = 8.4


def _normalize_time(date_value: str | None) -> str:
    if not date_value:
        return "00:00"

    try:
        return datetime.fromisoformat(date_value.replace("Z", "+00:00")).strftime("%H:%M")
    except (ValueError, TypeError):
        return "00:00"


def _build_default_prediction(fixture: dict[str, Any]) -> dict[str, Any]:
    home_team = fixture.get("teams", {}).get("home", {}).get("name", "Unknown Home")
    away_team = fixture.get("teams", {}).get("away", {}).get("name", "Unknown Away")
    league = fixture.get("league", {})

    probabilities = {"1": 33.3, "X": 33.3, "2": 33.4}

    return {
        "id": fixture.get("fixture", {}).get("id"),
        "time": _normalize_time(fixture.get("fixture", {}).get("date")),
        "league": league.get("name", "Unknown League"),
        "country": league.get("country", "Unknown"),
        "home_team": home_team,
        "away_team": away_team,
        "home_elo": DEFAULT_HOME_ELO,
        "away_elo": DEFAULT_AWAY_ELO,
        "home_form": DEFAULT_FORM,
        "away_form": DEFAULT_FORM,
        "probabilities": probabilities,
        "prediction": {
            "bet": "X",
            "confidence": 40.0,
            "level": "Ниска",
        },
        "expected_goals": DEFAULT_EXPECTED_GOALS,
        "over_25": DEFAULT_OVER_25,
        "expected_yellow_cards": DEFAULT_YELLOW,
        "expected_corners": DEFAULT_CORNERS,
        "details": {
            "home_goals_avg": round(DEFAULT_EXPECTED_GOALS / 2, 2),
            "away_goals_avg": round(DEFAULT_EXPECTED_GOALS / 2, 2),
            "home_yellow_cards_avg": round(DEFAULT_YELLOW / 2, 2),
            "away_yellow_cards_avg": round(DEFAULT_YELLOW / 2, 2),
            "home_corners_avg": round(DEFAULT_CORNERS / 2, 2),
            "away_corners_avg": round(DEFAULT_CORNERS / 2, 2),
            "home_form_score": 1.0,
            "away_form_score": 1.0,
        },
    }


def _write_cache(predictions: list[dict[str, Any]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "data": predictions,
        "timestamp": datetime.now().replace(microsecond=0).isoformat(),
    }
    CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_today_fixtures(api_key: str) -> list[dict[str, Any]]:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    headers = {"x-apisports-key": api_key}

    response = requests.get(
        API_URL,
        headers=headers,
        params={"date": today},
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    fixtures = data.get("response", [])
    if not isinstance(fixtures, list):
        return []

    return fixtures


def main() -> None:
    api_key = os.getenv("API_FOOTBALL_KEY", "").strip()

    if not api_key:
        print("API_FOOTBALL_KEY липсва. Записвам празен кеш.")
        _write_cache([])
        return

    try:
        fixtures = _fetch_today_fixtures(api_key)
        predictions = [_build_default_prediction(fixture) for fixture in fixtures if isinstance(fixture, dict)]
        _write_cache(predictions)
        print(f"Генерирани прогнози за {len(predictions)} мача.")
    except Exception as exc:  # noqa: BLE001
        print(f"Грешка при зареждане на прогнози: {exc}")
        _write_cache([])


if __name__ == "__main__":
    main()
