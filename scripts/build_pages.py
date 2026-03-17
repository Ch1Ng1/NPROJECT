from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "pages"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
CACHE_FILE = ROOT / "cache" / "predictions_cache.json"
PAGES_API_BASE_URL = os.getenv("PAGES_API_BASE_URL", "").strip().rstrip("/")


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


def _build_data() -> None:
    predictions: list[dict] = []

    if CACHE_FILE.exists():
        cache_json = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        data = cache_json.get("data", [])
        if isinstance(data, list):
            predictions = data

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
