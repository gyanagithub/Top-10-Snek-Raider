# Top-10-Snek-Raider

Scrapes the **Top 10 all-time raiders** from [snekraids.com](https://snekraids.com/) and displays them in a beautiful leaderboard UI and as a standalone PNG image.

## Preview

![Top 10 Snek Raiders UI](https://github.com/user-attachments/assets/99a52507-b41d-4732-a23d-3d32b65c6304)

## Files

| File | Description |
|---|---|
| `scraper.py` | Playwright scraper – navigates Community → All Time → List, extracts top 10 |
| `index.html` | Dark-themed leaderboard UI (reads `raiders.json`) |
| `generate_image.py` | Generates `leaderboard.png` using Pillow |
| `raiders.json` | Output data file produced by `scraper.py` |
| `leaderboard.png` | Output image produced by `generate_image.py` |
| `requirements.txt` | Python dependencies |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Scrape live data from snekraids.com
python scraper.py

# 3. Open the leaderboard UI in a browser
open index.html          # macOS
xdg-open index.html      # Linux
start index.html         # Windows

# 4. (Optional) Generate a PNG image
python generate_image.py
```

### Demo mode (no network required)

```bash
python scraper.py --demo          # writes sample data to raiders.json
python generate_image.py --demo   # generates leaderboard.png with sample data
```

## How the scraper works

1. Opens `https://snekraids.com/community` with a headless Chromium browser.
2. Finds the time-range filter and selects **All time**.
3. Clicks the **List** view button.
4. Extracts the top 10 raiders (rank, name, raid count, avatar URL).
5. Saves the results to `raiders.json`.

## Navigation path

> Community → *All time* (dropdown) → List → Top 10
