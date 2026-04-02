"""
Scraper for snekraids.com - Fetches the top 10 all-time raiders
from the Community section and saves results to raiders.json.

Usage:
    python scraper.py               # Scrape live data
    python scraper.py --demo        # Generate demo data (no network needed)
"""

import argparse
import json
import re
import sys
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent / "raiders.json"
BASE_URL = "https://snekraids.com"
COMMUNITY_URL = f"{BASE_URL}/community"


def scrape_top_raiders() -> list[dict]:
    """Navigate snekraids.com/community, select 'All time', switch to List
    view, and return the top 10 raiders as a list of dicts."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("Error: playwright is not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    raiders = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )
        page = context.new_page()

        print(f"Navigating to {COMMUNITY_URL} …")
        try:
            page.goto(COMMUNITY_URL, wait_until="networkidle", timeout=30_000)
        except PWTimeout:
            page.goto(COMMUNITY_URL, wait_until="domcontentloaded", timeout=30_000)

        # ── 1. Select "All time" from the time-range dropdown ──────────────
        print("Selecting 'All time' from the dropdown …")
        try:
            # Try a <select> element first
            selects = page.query_selector_all("select")
            found_select = False
            for sel in selects:
                opts = sel.query_selector_all("option")
                for opt in opts:
                    if "all" in (opt.inner_text() or "").lower():
                        sel.select_option(value=opt.get_attribute("value") or opt.inner_text())
                        found_select = True
                        break
                if found_select:
                    break

            if not found_select:
                # Try button/clickable dropdown
                time_triggers = page.query_selector_all(
                    "[class*='dropdown'], [class*='filter'], [class*='period'], [class*='time']"
                )
                for trigger in time_triggers:
                    text = (trigger.inner_text() or "").lower()
                    if any(k in text for k in ("week", "month", "all", "time")):
                        trigger.click()
                        page.wait_for_timeout(500)
                        all_time_opt = page.get_by_text(
                            re.compile(r"^all\s*time$", re.IGNORECASE)
                        ).first
                        if all_time_opt and all_time_opt.is_visible():
                            all_time_opt.click()
                            break
        except Exception as exc:
            print(f"  Warning: could not set time filter – {exc}")

        page.wait_for_timeout(1000)

        # ── 2. Switch to "List" view ────────────────────────────────────────
        print("Switching to List view …")
        try:
            list_btn = page.query_selector(
                "button:has-text('List'), a:has-text('List'), [aria-label*='list' i]"
            )
            if list_btn:
                list_btn.click()
                page.wait_for_timeout(1000)
        except Exception as exc:
            print(f"  Warning: could not click List view – {exc}")

        # ── 3. Extract top-10 raiders ───────────────────────────────────────
        print("Extracting top 10 raiders …")
        page.wait_for_timeout(1500)

        # Attempt 1: structured table rows
        rows = page.query_selector_all("table tbody tr")
        if rows:
            for i, row in enumerate(rows[:10], start=1):
                cells = row.query_selector_all("td")
                name = cells[1].inner_text().strip() if len(cells) > 1 else f"Raider {i}"
                count_text = cells[-1].inner_text().strip() if cells else "0"
                count = int("".join(filter(str.isdigit, count_text)) or 0)
                avatar_el = row.query_selector("img")
                avatar = avatar_el.get_attribute("src") if avatar_el else None
                raiders.append({"rank": i, "name": name, "raids": count, "avatar": avatar})

        # Attempt 2: list items / cards
        if not raiders:
            cards = page.query_selector_all(
                "[class*='raider'], [class*='leaderboard'] li, "
                "[class*='ranking'] li, [class*='community'] li"
            )
            for i, card in enumerate(cards[:10], start=1):
                name_el = card.query_selector(
                    "[class*='name'], [class*='username'], [class*='user'], strong, b, h3, h4"
                )
                count_el = card.query_selector(
                    "[class*='count'], [class*='raids'], [class*='score'], span"
                )
                avatar_el = card.query_selector("img")
                name = name_el.inner_text().strip() if name_el else f"Raider {i}"
                count_text = count_el.inner_text().strip() if count_el else "0"
                count = int("".join(filter(str.isdigit, count_text)) or 0)
                avatar = avatar_el.get_attribute("src") if avatar_el else None
                raiders.append({"rank": i, "name": name, "raids": count, "avatar": avatar})

        # Attempt 3: generic ordered list / numbered items
        if not raiders:
            items = page.query_selector_all("ol li, [class*='rank'] [class*='item']")
            for i, item in enumerate(items[:10], start=1):
                text = item.inner_text().strip()
                raiders.append({"rank": i, "name": text, "raids": 0, "avatar": None})

        browser.close()

    # Make avatar URLs absolute
    for r in raiders:
        if r.get("avatar") and r["avatar"].startswith("/"):
            r["avatar"] = BASE_URL + r["avatar"]

    return raiders


def demo_data() -> list[dict]:
    """Return a set of placeholder raiders for UI demonstration."""
    return [
        {"rank": 1,  "name": "SnekMaster3000", "raids": 487, "avatar": None},
        {"rank": 2,  "name": "RaidQueen99",     "raids": 412, "avatar": None},
        {"rank": 3,  "name": "Cobra_Strike",    "raids": 378, "avatar": None},
        {"rank": 4,  "name": "VenomViper",      "raids": 341, "avatar": None},
        {"rank": 5,  "name": "PythonProwler",   "raids": 299, "avatar": None},
        {"rank": 6,  "name": "AnacondaAce",     "raids": 265, "avatar": None},
        {"rank": 7,  "name": "SerpentSurge",    "raids": 241, "avatar": None},
        {"rank": 8,  "name": "Sidewinder_Sam",  "raids": 218, "avatar": None},
        {"rank": 9,  "name": "MambaRaider",     "raids": 196, "avatar": None},
        {"rank": 10, "name": "TwilightBoa",     "raids": 174, "avatar": None},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape top-10 Snek Raiders")
    parser.add_argument(
        "--demo", action="store_true",
        help="Use placeholder data instead of live scraping"
    )
    args = parser.parse_args()

    if args.demo:
        print("Using demo data …")
        raiders = demo_data()
    else:
        raiders = scrape_top_raiders()
        if not raiders:
            print("No raiders found – falling back to demo data.")
            raiders = demo_data()

    OUTPUT_FILE.write_text(json.dumps({"raiders": raiders}, indent=2))
    print(f"Saved {len(raiders)} raiders → {OUTPUT_FILE}")

    # Pretty-print the leaderboard to stdout
    print("\n🐍  Top 10 Snek Raiders (All Time)")
    print("─" * 40)
    for r in raiders:
        print(f"  #{r['rank']:>2}  {r['name']:<25}  {r['raids']:>4} raids")


if __name__ == "__main__":
    main()
