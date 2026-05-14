from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
import shutil
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from requests import RequestException

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "pages"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
CACHE_FILE = ROOT / "cache" / "predictions_cache.json"
PAGES_API_BASE_URL = os.getenv("PAGES_API_BASE_URL", "").strip().rstrip("/")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
# Default timezone follows the app's primary Bulgaria audience and API queries in Europe/Sofia.
PAGES_TIMEZONE = os.getenv("PAGES_TIMEZONE", "Europe/Sofia")
logger = logging.getLogger(__name__)
REMOTE_API_TIMEOUT_SECONDS = 20


def _prepare_pages_dir() -> None:
    if PAGES_DIR.exists():
        shutil.rmtree(PAGES_DIR)
    (PAGES_DIR / "data").mkdir(parents=True, exist_ok=True)


def _build_index() -> None:
    source = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    output = source.replace('href="/static/styles.css"', 'href="./styles.css"')
    output = output.replace('src="/static/script.js"', 'src="./script.js"')
    config_script = (
        "<script>window.__APP_CONFIG__ = "
        + json.dumps(
            {
                "apiBaseUrl": PAGES_API_BASE_URL,
                "staticDataUrl": "./data/predictions.json",
            },
            ensure_ascii=False,
        )
        + ";</script>"
    )
    output = output.replace("</head>", f"    {config_script}\n</head>")
    (PAGES_DIR / "index.html").write_text(output, encoding="utf-8")


def _build_404() -> None:
    source = (TEMPLATES_DIR / "404.html").read_text(encoding="utf-8")
    output = source.replace('href="/static/styles.css"', 'href="./styles.css"')
    output = output.replace('href="/"', 'href="./"')
    (PAGES_DIR / "404.html").write_text(output, encoding="utf-8")


def _copy_assets() -> None:
    shutil.copy2(STATIC_DIR / "styles.css", PAGES_DIR / "styles.css")
    shutil.copy2(STATIC_DIR / "script.js", PAGES_DIR / "script.js")
    (PAGES_DIR / ".nojekyll").write_text("", encoding="utf-8")


def _current_pages_date() -> date:
    try:
        return datetime.now(ZoneInfo(PAGES_TIMEZONE)).date()
    except ZoneInfoNotFoundError:
        logger.warning("PAGES_TIMEZONE '%s' not found, falling back to UTC", PAGES_TIMEZONE)
        return datetime.now(ZoneInfo("UTC")).date()


def _build_data() -> None:
    predictions: list[dict] = []

    if CACHE_FILE.exists():
        cache_json = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        timestamp = cache_json.get("timestamp")
        data = cache_json.get("data", [])
        is_today_cache = False
        if timestamp:
            try:
                cache_date = datetime.fromisoformat(timestamp).date()
                is_today_cache = cache_date == _current_pages_date()
            except ValueError:
                logger.warning("Invalid cache timestamp '%s', skipping cache reuse", timestamp)
        if isinstance(data, list) and is_today_cache:
            predictions = data

    if not predictions and PAGES_API_BASE_URL:
        try:
            response = requests.get(
                f"{PAGES_API_BASE_URL}/api/predictions", timeout=REMOTE_API_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, list):
                predictions = payload
            elif isinstance(payload, dict):
                if payload.get("success") and isinstance(payload.get("data"), list):
                    predictions = payload["data"]
                elif isinstance(payload.get("predictions"), list):
                    predictions = payload["predictions"]
                elif isinstance(payload.get("data"), dict) and isinstance(
                    payload["data"].get("predictions"), list
                ):
                    predictions = payload["data"]["predictions"]
        except (RequestException, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Failed to fetch predictions from remote API base URL: %s", exc)

    if not predictions and API_FOOTBALL_KEY:
        try:
            from predictor import SmartPredictor

            predictor = SmartPredictor(api_key=API_FOOTBALL_KEY)
            predictions = predictor.get_today_predictions()
            if not isinstance(predictions, list):
                predictions = []
        except ImportError as exc:
            logger.warning("Cannot import SmartPredictor dependencies for Pages build: %s", exc)
            predictions = []
        except RequestException as exc:
            logger.warning("API request failed while generating fresh predictions: %s", exc)
            predictions = []
        except ValueError as exc:
            logger.warning("Invalid API_FOOTBALL_KEY or prediction data for Pages build: %s", exc)
            predictions = []

    (PAGES_DIR / "data" / "predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    _prepare_pages_dir()
    _build_index()
    _build_404()
    _copy_assets()
    _build_data()
    print(f"GitHub Pages build generated in: {PAGES_DIR}")


if __name__ == "__main__":
    main()
