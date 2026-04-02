"""
Generate a leaderboard image (leaderboard.png) from raiders.json
using Pillow (PIL).

Usage:
    python generate_image.py              # reads raiders.json
    python generate_image.py --demo       # use built-in demo data
    python generate_image.py --out path   # custom output path
"""

import argparse
import json
from pathlib import Path

RAIDERS_JSON = Path(__file__).parent / "raiders.json"
OUTPUT_PNG   = Path(__file__).parent / "leaderboard.png"

# ── Colour palette ───────────────────────────────────────────────────────────
BG          = (13,  15,  26)      # #0d0f1a
SURFACE     = (22,  25,  41)      # #161929
SURFACE2    = (30,  35,  56)      # #1e2338
ACCENT      = (127, 255,  42)     # #7fff2a
ACCENT2     = (61,  247, 160)     # #3df7a0
GOLD        = (255, 215,   0)
SILVER      = (192, 192, 192)
BRONZE      = (205, 127,  50)
TEXT        = (232, 236, 245)
TEXT_MUTED  = (122, 134, 168)
BORDER      = (42,  48,  80)

MEDALS = ['🥇', '🥈', '🥉']


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_rounded_rect(draw, xy, fill, radius=12):
    from PIL import ImageDraw
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius * 2, y0 + radius * 2], fill=fill)
    draw.ellipse([x1 - radius * 2, y0, x1, y0 + radius * 2], fill=fill)
    draw.ellipse([x0, y1 - radius * 2, x0 + radius * 2, y1], fill=fill)
    draw.ellipse([x1 - radius * 2, y1 - radius * 2, x1, y1], fill=fill)


def generate_image(raiders: list[dict], out_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("Error: pillow is not installed. Run: pip install pillow")

    W           = 640
    ROW_H       = 56
    PADDING     = 24
    HEADER_H    = 110
    FOOTER_H    = 40
    N           = min(10, len(raiders))
    H           = HEADER_H + N * ROW_H + PADDING + FOOTER_H

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Try to load fonts; fall back to default ──────────────────────────────
    import sys as _sys

    FONT_PATHS = {
        "bold": [],
        "regular": [],
    }
    if _sys.platform == "win32":
        FONT_PATHS["bold"]    = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"]
        FONT_PATHS["regular"] = ["C:/Windows/Fonts/arial.ttf",   "C:/Windows/Fonts/calibri.ttf"]
    elif _sys.platform == "darwin":
        FONT_PATHS["bold"]    = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
        ]
        FONT_PATHS["regular"] = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    else:
        FONT_PATHS["bold"]    = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        FONT_PATHS["regular"] = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

    def font(size, bold=False):
        for path in FONT_PATHS["bold" if bold else "regular"]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    f_title   = font(26, bold=True)
    f_sub     = font(13)
    f_rank    = font(17, bold=True)
    f_name    = font(15, bold=True)
    f_count   = font(17, bold=True)
    f_label   = font(11)
    f_footer  = font(11)

    # ── Header ───────────────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, HEADER_H], fill=SURFACE)
    draw.rectangle([0, HEADER_H - 1, W, HEADER_H], fill=BORDER)

    title = "Top 10 Snek Raiders"
    bbox = draw.textbbox((0, 0), title, font=f_title)
    tw = bbox[2] - bbox[0]
    x0 = (W - tw) // 2
    # Gradient-ish: draw title in accent colour
    draw.text((x0, 18), title, fill=ACCENT, font=f_title)

    sub = "snekraids.com  •  Community  •  All Time"
    bbox2 = draw.textbbox((0, 0), sub, font=f_sub)
    sw = bbox2[2] - bbox2[0]
    draw.text(((W - sw) // 2, 54), sub, fill=TEXT_MUTED, font=f_sub)

    # "All Time" badge
    badge = "ALL TIME"
    bbox3 = draw.textbbox((0, 0), badge, font=f_sub)
    bw = bbox3[2] - bbox3[0] + 24
    bh = bbox3[3] - bbox3[1] + 10
    bx = (W - bw) // 2
    by = 76
    draw_rounded_rect(draw, (bx, by, bx + bw, by + bh), ACCENT, radius=8)
    draw.text((bx + 12, by + 5), badge, fill=BG, font=f_sub)

    # ── Rows ──────────────────────────────────────────────────────────────────
    max_raids = max((r["raids"] for r in raiders[:N]), default=1) or 1

    for idx, raider in enumerate(raiders[:N]):
        rank   = raider["rank"]
        name   = raider["name"]
        raids  = raider["raids"]
        y      = HEADER_H + idx * ROW_H

        row_fill = SURFACE
        if rank == 1:
            row_fill = (18, 17, 6)
        elif rank == 2:
            row_fill = (16, 17, 18)
        elif rank == 3:
            row_fill = (18, 15, 10)

        draw.rectangle([0, y, W, y + ROW_H - 1], fill=row_fill)

        # Left accent bar for podium
        bar_color = None
        if rank == 1: bar_color = GOLD
        elif rank == 2: bar_color = SILVER
        elif rank == 3: bar_color = BRONZE
        if bar_color:
            draw.rectangle([0, y, 3, y + ROW_H - 1], fill=bar_color)

        # Separator
        draw.rectangle([0, y + ROW_H - 1, W, y + ROW_H], fill=BORDER)

        # Rank / medal
        if rank <= 3:
            rank_str = ['1st', '2nd', '3rd'][rank - 1]
            rank_col = [GOLD, SILVER, BRONZE][rank - 1]
        else:
            rank_str = f"#{rank}"
            rank_col = TEXT_MUTED

        draw.text((PADDING, y + 18), rank_str, fill=rank_col, font=f_rank)

        # Avatar placeholder (circle with initials)
        av_x = PADDING + 52
        av_cy = y + ROW_H // 2
        av_r  = 18
        border_col = bar_color or BORDER
        draw.ellipse(
            [av_x, av_cy - av_r, av_x + av_r * 2, av_cy + av_r],
            fill=SURFACE2, outline=border_col, width=2
        )
        initials = "".join(p[0] for p in name.replace("_", " ").split()[:2]).upper() or "?"
        ib = draw.textbbox((0, 0), initials, font=f_label)
        iw, ih = ib[2] - ib[0], ib[3] - ib[1]
        draw.text(
            (av_x + av_r - iw // 2, av_cy - ih // 2),
            initials, fill=TEXT, font=f_label
        )

        # Name
        name_x = av_x + av_r * 2 + 12
        draw.text((name_x, y + 10), name, fill=TEXT, font=f_name)

        # Progress bar under name
        bar_y  = y + 36
        bar_w  = W - name_x - 120
        bar_pct = raids / max_raids
        draw.rectangle([name_x, bar_y, name_x + bar_w, bar_y + 4], fill=SURFACE2)
        if bar_pct > 0:
            fill_c = lerp_color(ACCENT, ACCENT2, idx / max(N - 1, 1))
            draw.rectangle([name_x, bar_y, name_x + int(bar_w * bar_pct), bar_y + 4], fill=fill_c)

        # Raid count
        count_str = f"{raids:,}"
        cb = draw.textbbox((0, 0), count_str, font=f_count)
        cw = cb[2] - cb[0]
        cx = W - PADDING - cw
        draw.text((cx, y + 10), count_str, fill=ACCENT, font=f_count)

        label_str = "raids"
        lb = draw.textbbox((0, 0), label_str, font=f_label)
        lw = lb[2] - lb[0]
        lx = W - PADDING - lw
        draw.text((lx, y + 34), label_str, fill=TEXT_MUTED, font=f_label)

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = HEADER_H + N * ROW_H + 10
    footer_str = "snekraids.com  •  github.com/gyanagithub/Top-10-Snek-Raider"
    fb = draw.textbbox((0, 0), footer_str, font=f_footer)
    fw = fb[2] - fb[0]
    draw.text(((W - fw) // 2, fy), footer_str, fill=TEXT_MUTED, font=f_footer)

    img.save(out_path)
    print(f"Image saved → {out_path}  ({W}×{H} px)")


def demo_data() -> list[dict]:
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
    parser = argparse.ArgumentParser(description="Generate Top-10 Snek Raiders leaderboard image")
    parser.add_argument("--demo", action="store_true", help="Use built-in demo data")
    parser.add_argument("--out", default=str(OUTPUT_PNG), help="Output file path")
    args = parser.parse_args()

    if args.demo:
        raiders = demo_data()
    elif RAIDERS_JSON.exists():
        data = json.loads(RAIDERS_JSON.read_text())
        raiders = data.get("raiders", data)
    else:
        print("No raiders.json found – using demo data. Run scraper.py first for live data.")
        raiders = demo_data()

    generate_image(raiders, Path(args.out))


if __name__ == "__main__":
    main()
