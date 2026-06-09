#!/usr/bin/env python3
"""
market_bot.py — Daily VN-Index market commentary generator.

Fetches VN-Index data via vnstock, calls MiniMax M3 via Ollama Cloud API,
and writes a markdown file matching the Astro content collection schema.

Usage:
    python market_bot.py                  # today's commentary
    python market_bot.py --date 2026-06-09  # specific date

Environment:
    MINIMAX_API_KEY  — Ollama Cloud API key (required)
    LLM_BASE_URL     — API base URL (default: https://ollama.com/api)
    LLM_MODEL        — Model name (default: minimax-m3)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONTENT_DIR = Path(__file__).parent / "src" / "content" / "market-views"
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://ollama.com/api")
LLM_MODEL = os.environ.get("LLM_MODEL", "minimax-m3")
ICT_OFFSET = timedelta(hours=7)  # UTC+7

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_vnindex_data(date_str: str) -> dict:
    """Fetch VN-Index OHLCV data for a given date using vnstock.

    Returns dict with keys: close, change_pts, change_pct, volume, value.
    Falls back to estimation if vnstock fails.
    """
    try:
        from vnstock import Market

        mkt = Market()
        # Fetch 5 days to ensure we get the trading day (weekends/holidays)
        end_date = date_str
        start_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )

        df = mkt.index("VNINDEX").ohlcv(start=start_date, end=end_date)

        if df is None or df.empty:
            print(f"Warning: vnstock returned empty data for {date_str}, using fallback")
            return _fallback_data(date_str)

        # Take the last row (should be the requested date or nearest trading day)
        last = df.iloc[-1]

        close = float(last["close"])
        # Calculate change from previous day
        if len(df) >= 2:
            prev_close = float(df.iloc[-2]["close"])
            change_pts = round(close - prev_close, 2)
            change_pct = round((close - prev_close) / prev_close * 100, 2)
        else:
            change_pts = 0.0
            change_pct = 0.0

        # Volume and value
        volume = int(last.get("volume", 0))
        value = int(last.get("value", 0))

        # Liquidity in billions VND (value is typically already in VND)
        liquidity_bn = round(value / 1e9, 0) if value > 0 else 0

        print(f"OK: vnstock data fetched: VN-Index {close} ({change_pts:+.2f} pts, {change_pct:+.2f}%)")

        return {
            "close": close,
            "change_pts": change_pts,
            "change_pct": change_pct,
            "volume": volume,
            "liquidity_bn_vnd": int(liquidity_bn),
        }

    except Exception as e:
        print(f"Warning: vnstock fetch failed: {e}")
        return _fallback_data(date_str)


def fetch_foreign_flow(date_str: str) -> int:
    """Fetch aggregate foreign net flow for the date.

    Returns net foreign flow in billions VND (negative = net selling).
    Falls back to 0 if unavailable.
    """
    try:
        from vnstock import Trading

        trading = Trading(symbol="VNINDEX", source="VCI")
        df = trading.price_board(symbols_list=["VNINDEX"])

        # Look for foreign net columns
        # Column names vary by vnstock version, try common patterns
        for col in ["foreign_net_value", "fr_net_val", "nmTotalTradedValue"]:
            if col in df.columns:
                val = float(df.iloc[0][col])
                return int(round(val / 1e9, 0))  # Convert to billions

        # If no direct column, try aggregating buy/sell
        for buy_col, sell_col in [
            ("foreign_buy_value", "foreign_sell_value"),
            ("fr_buy_val", "fr_sell_val"),
        ]:
            if buy_col in df.columns and sell_col in df.columns:
                net = float(df.iloc[0][buy_col]) - float(df.iloc[0][sell_col])
                return int(round(net / 1e9, 0))

        print("Warning: Could not find foreign flow columns, defaulting to 0")
        return 0

    except Exception as e:
        print(f"Warning: Foreign flow fetch failed: {e}, defaulting to 0")
        return 0


def _fallback_data(date_str: str) -> dict:
    """Return placeholder data when vnstock is unavailable.

    The LLM will be told these are estimates and should note that in the commentary.
    """
    print(f"Warning: Using fallback data for {date_str}")
    return {
        "close": 0,
        "change_pts": 0,
        "change_pct": 0,
        "volume": 0,
        "liquidity_bn_vnd": 0,
    }


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def generate_commentary(data: dict, foreign_net: int, date_str: str) -> str:
    """Call MiniMax M3 via Ollama Cloud API to generate market commentary markdown."""

    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY or LLM_API_KEY environment variable not set")
        sys.exit(1)

    # Determine session tone based on data
    if data["close"] == 0:
        tone_hint = "neutral"
    elif data["change_pct"] > 0.3:
        tone_hint = "positive"
    elif data["change_pct"] < -0.3:
        tone_hint = "negative"
    else:
        tone_hint = "neutral"

    # Format date for title: "Jun 9"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_display = dt.strftime("%b %d").replace(" 0", " ")

    is_estimated = data["close"] == 0
    data_note = ""
    if is_estimated:
        data_note = """
IMPORTANT: Real market data is unavailable today. You must generate realistic but
clearly hypothetical data for the frontmatter. Use plausible VN-Index values around
1270-1300 with small changes. In the body text, explicitly note that this is a
simulated commentary due to data unavailability.
"""

    prompt = f"""You are a Vietnam capital markets analyst writing a daily VN-Index
market commentary for a professional finance portfolio website. Your audience includes
PE/VC fund managers, M&A practitioners, and finance recruiters.

Today's data ({date_str}):
- VN-Index Close: {data['close']}
- Change (pts): {data['change_pts']:+.2f}
- Change (%): {data['change_pct']:+.2f}%
- Market Liquidity: {data['liquidity_bn_vnd']} billion VND
- Foreign Net Flow: {foreign_net} billion VND
- Session tone: {tone_hint}
{data_note}
Write a markdown file with EXACTLY this structure:

1. YAML frontmatter (between --- delimiters) with these 8 fields:
   - title: "VN-Index {date_display}: {{{{descriptive headline}}}}"
   - date: "{date_str}" (string)
   - vn_index_close: {data['close']} (number)
   - vn_index_change_pts: {data['change_pts']} (number)
   - vn_index_change_pct: {data['change_pct']} (number)
   - liquidity_bn_vnd: {data['liquidity_bn_vnd']} (number)
   - foreign_net_bn_vnd: {foreign_net} (number, negative for net selling)
   - session_tone: exactly one of "positive", "negative", or "neutral"

2. Body with exactly 4 sections (## headings):
   ## Session Overview -- High-level summary referencing the close level, point change,
     percentage change, and breadth (advancers vs decliners ratio when possible).

   ## Key Drivers -- Bulleted list of sector/stock-level drivers. Use specific tickers
     (VCB, BID, CTG for banking; HPG for steel; VNM, MSN for consumer; VIC, VRE for
     real estate). Quantify contributions where plausible.

   ## Foreign Flow -- Narrative on net foreign buying/selling with magnitude and
     interpretation (index rebalancing vs. directional outflows/inflows).

   ## Technical Outlook -- Support/resistance levels, moving average references, and
     forward-looking tone. Keep it analytical.

Rules:
- Professional, analytical tone -- NOT hype or clickbait.
- Use finance-domain accurate English.
- End the Technical Outlook section with: "*Academic exercise -- not investment advice.*"
- Output ONLY the markdown file content. No explanations outside the markdown.
- The session_tone must be exactly: "positive" if change_pct > 0.3, "negative" if
  change_pct < -0.3, "neutral" otherwise.
- All numeric frontmatter fields must be raw numbers (no quotes, no units)."""

    # Call Ollama Cloud API (/api/chat endpoint)
    url = f"{LLM_BASE_URL}/chat"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: LLM API returned HTTP {e.code}: {body[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: LLM API call failed: {e}")
        sys.exit(1)

    text = result.get("message", {}).get("content", "").strip()

    # Strip any leading/trailing markdown code fences if the LLM adds them
    if text.startswith("```markdown"):
        text = text[len("```markdown"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# File write + validation
# ---------------------------------------------------------------------------


def validate_frontmatter(content: str, date_str: str) -> bool:
    """Basic validation that the generated file has correct frontmatter fields."""
    if not content.startswith("---"):
        print("ERROR: Generated content does not start with --- frontmatter delimiter")
        return False

    end = content.find("---", 3)
    if end == -1:
        print("ERROR: Could not find closing --- frontmatter delimiter")
        return False

    frontmatter = content[3:end].strip()
    required_fields = [
        "title",
        "date",
        "vn_index_close",
        "vn_index_change_pts",
        "vn_index_change_pct",
        "liquidity_bn_vnd",
        "foreign_net_bn_vnd",
        "session_tone",
    ]

    for field in required_fields:
        if field not in frontmatter:
            print(f"ERROR: Missing required frontmatter field: {field}")
            return False

    # Check session_tone contains one of the valid values
    valid_tones = ["positive", "negative", "neutral"]
    found_tone = False
    for tone in valid_tones:
        if tone in frontmatter:
            found_tone = True
            break

    if not found_tone:
        print(f"ERROR: session_tone must be one of {valid_tones}")
        return False

    return True


def write_file(content: str, date_str: str) -> Path:
    """Write the markdown file to the content directory."""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CONTENT_DIR / f"{date_str}.md"

    if filepath.exists():
        print(f"Warning: File {filepath} already exists, overwriting")

    filepath.write_text(content, encoding="utf-8")
    print(f"OK: Written: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Generate daily VN-Index market commentary")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today ICT)", default=None)
    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        # Use ICT (UTC+7) for date -- market operates in Vietnam time
        utc_now = datetime.utcnow()
        ict_now = utc_now + ICT_OFFSET
        date_str = ict_now.strftime("%Y-%m-%d")

    print(f"Date: {date_str}")

    # 1. Fetch data
    data = fetch_vnindex_data(date_str)

    # 2. Fetch foreign flow
    foreign_net = fetch_foreign_flow(date_str) if data["close"] != 0 else 0

    # 3. Generate commentary via LLM
    content = generate_commentary(data, foreign_net, date_str)

    # 4. Validate
    if not validate_frontmatter(content, date_str):
        print("ERROR: Generated content failed validation, exiting")
        sys.exit(1)

    # 5. Write file
    filepath = write_file(content, date_str)

    print(f"\nDone! Commentary written to: {filepath}")
    print(f"Next: git add -A && git commit -m 'daily: market commentary {date_str}' && git push")


if __name__ == "__main__":
    main()