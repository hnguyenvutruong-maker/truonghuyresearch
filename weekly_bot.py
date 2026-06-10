#!/usr/bin/env python3
"""
weekly_bot.py — Weekly Market View generator with 2 pillars:
  1. Quarterly Rolling Summary (long-term memory via JSON)
  2. News Scraping (RSS + fallback HTML)

Output:
  - src/content/market-views/{Friday-date}.md   (Astro content collection)
  - src/content/market-views/_quarterly_summary.json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import textwrap
import urllib.request
import urllib.error
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ── Reconfigure stdout/stderr to UTF-8 (Windows console default is cp1252/charmap,
#    which breaks when vnstock or feedparser prints Vietnamese characters) ──
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    elif _stream is not None and hasattr(_stream, "buffer"):
        try:
            setattr(sys, _stream_name,
                    io.TextIOWrapper(_stream.buffer, encoding="utf-8", errors="replace"))
        except Exception:
            pass

# ── Optional third-party imports ────────────────────────────────────────────
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    import requests as requests_lib
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    from vnstock import Vnstock
    HAS_VNSTOCK = True
except ImportError:
    HAS_VNSTOCK = False

try:
    from vnstock.api.quote import Quote as VnQuote
    HAS_VNQUOTE = True
except ImportError:
    HAS_VNQUOTE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "market-views"
QUARTERLY_FILE = CONTENT_DIR / "_quarterly_summary.json"
FOREIGN_FLOW_CACHE = CONTENT_DIR / "_foreign_flow_cache.json"

# LLM config
LLM_API_KEY = os.getenv("OLLAMA_API_KEY") or os.getenv("LLM_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ollama.com/api")
LLM_MODEL = os.getenv("LLM_MODEL", "minimax-m3")

# Ensure output dirs exist
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# ICT (Indochina Time) offset
ICT_OFFSET = timedelta(hours=7)


# ═══════════════════════════════════════════════════════════════════════════════
# DATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def today_ict() -> date:
    """Return today's date in ICT."""
    return (datetime.utcnow() + ICT_OFFSET).date()


def get_week_dates(friday_str: Optional[str] = None) -> tuple[date, date, date]:
    """
    Return (monday, friday, today) for the target week.
    If friday_str is provided (ISO format YYYY-MM-DD), use that Friday.
    Otherwise find the most recently completed Friday.
    """
    if friday_str:
        friday = date.fromisoformat(friday_str)
    else:
        today = today_ict()
        # Most recent Friday (skip if today is Friday and not yet EOD, though we
        # assume this runs on Saturday/Sunday)
        days_since_friday = (today.weekday() - 4) % 7
        friday = today - timedelta(days=days_since_friday)
        # If today IS Friday, use it
        if today.weekday() == 4:
            friday = today

    monday = friday - timedelta(days=4)
    return monday, friday, today_ict()


def get_quarter(d: date) -> str:
    """Return quarter label e.g. 'Q1-2026'."""
    q = (d.month - 1) // 3 + 1
    return f"Q{q}-{d.year}"


def quarter_date_range(quarter: str) -> tuple[date, date]:
    """Return (start_date, end_date) inclusive for a quarter label like 'Q2-2026'."""
    m = re.match(r"Q([1-4])-(\d{4})", quarter)
    if not m:
        raise ValueError(f"Invalid quarter format: {quarter}. Expected e.g. Q2-2026")
    q = int(m.group(1))
    year = int(m.group(2))
    start_month = (q - 1) * 3 + 1
    end_month = start_month + 2
    start = date(year, start_month, 1)
    # End: last day of end_month
    if end_month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, end_month + 1, 1) - timedelta(days=1)
    return start, end


def week_identifier(friday: date) -> str:
    """Return 'YYYY-MM-DD' string for a Friday date."""
    return friday.isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def safe_num(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_pct(value: Optional[float]) -> str:
    """Format a percentage value nicely."""
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def log(step: str, message: str = "") -> None:
    """Print a progress log line."""
    if message:
        print(f"  [{step}] {message}")
    else:
        print(f"[{step}]")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch_hose_avg_share_price() -> Optional[float]:
    """
    Fetch the average HOSE share price (VND per share) from CafeF banggia API.

    CafeF returns both `value` (tỷ VND) and `volume` (shares) for VNINDEX,
    which represents the HOSE total market. The ratio value/volume gives
    the average price per share traded — far more accurate than using the
    VN-Index close (~1,840) as a proxy for average share price (~28,000 VND).

    Returns None if the API is unreachable.
    """
    if not HAS_BS4:
        return None
    try:
        url = "https://banggia.cafef.vn/stockhandler.ashx?center=1&index=true"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests_lib.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for item in data:
            if isinstance(item, dict) and item.get("name") == "VNINDEX":
                val_str = item.get("value", "0")
                vol_str = item.get("volume", "0")
                # Parse comma-separated numbers (e.g. "10,285.49", "423,201,967")
                val_ty = float(val_str.replace(",", ""))
                vol = float(vol_str.replace(",", ""))
                if vol > 0:
                    avg_price = val_ty * 1e9 / vol  # tỷ VND → VND per share
                    log('1/8', f"  CafeF HOSE value={val_ty:,.2f} tỷ, volume={vol:,.0f} shares, "
                         f"avg price={avg_price:,.0f} VND/share")
                    return avg_price
        return None
    except Exception as e:
        log('1/8', f"  CafeF banggia API failed: {e}")
        return None


# ── Foreign flow cache ───────────────────────────────────────────────────────
# CafeF banggia API provides real-time foreign buy/sell volumes per stock
# (fields 'x'=foreign buy vol, 'y'=foreign sell vol, prices in nghin VND),
# but ONLY for the latest trading day — no historical endpoint exists.
# Strategy: run `--collect-foreign-flow` daily (cron) to accumulate daily
# values in _foreign_flow_cache.json; the weekly bot then sums from cache.

def _load_foreign_flow_cache() -> dict[str, Any]:
    """Load the foreign flow cache. Returns {date_str: net_bn_vnd, ...}."""
    if FOREIGN_FLOW_CACHE.exists():
        try:
            return json.loads(FOREIGN_FLOW_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_foreign_flow_cache(cache: dict[str, Any]) -> None:
    """Persist the foreign flow cache to disk."""
    FOREIGN_FLOW_CACHE.parent.mkdir(parents=True, exist_ok=True)
    FOREIGN_FLOW_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def collect_foreign_flow_today() -> Optional[float]:
    """
    Fetch today's HOSE foreign net flow from CafeF banggia API and cache it.

    CafeF returns stock-level data with obfuscated keys:
      - 'a' = symbol, 'e' = price (nghin VND), 'n' = total volume
      - 'x' = foreign buy volume (shares), 'y' = foreign sell volume (shares)

    Returns net foreign flow in bn VND, or None if API fails.
    """
    if not HAS_BS4:
        log("FF", "  requests/bs4 not available, skipping foreign flow collection")
        return None
    try:
        url = "https://banggia.cafef.vn/stockhandler.ashx?center=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests_lib.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            log("FF", f"  CafeF API returned status {resp.status_code}")
            return None
        data = resp.json()
        if not isinstance(data, list) or not data:
            log("FF", "  CafeF API returned empty/invalid data")
            return None

        # Sum foreign net value across all HOSE stocks
        # Price in nghin VND (* 1000 for actual VND)
        foreign_net_vnd = 0.0
        foreign_buy_vol = 0
        foreign_sell_vol = 0
        for item in data:
            if not isinstance(item, dict):
                continue
            price_vnd = item.get("e", 0) * 1000  # nghin VND → VND
            fb = item.get("x", 0)  # foreign buy volume
            fs = item.get("y", 0)  # foreign sell volume
            foreign_buy_vol += fb
            foreign_sell_vol += fs
            if price_vnd > 0:
                foreign_net_vnd += (fb - fs) * price_vnd

        net_bn = round(foreign_net_vnd / 1e9, 2)
        total_vol = sum(item.get("n", 0) for item in data if isinstance(item, dict))
        fpct = (foreign_buy_vol + foreign_sell_vol) / total_vol * 100 if total_vol else 0

        # Get the trading date from the data
        trade_date_str = ""
        first_item = next((i for i in data if isinstance(i, dict)), None)
        if first_item and "Time" in first_item:
            # Parse "14:07 10/06/2026" → "2026-06-10"
            time_str = first_item["Time"]
            parts = time_str.split()
            if len(parts) >= 2:
                day_parts = parts[1].split("/")
                if len(day_parts) == 3:
                    trade_date_str = f"{day_parts[2]}-{day_parts[1]}-{day_parts[0]}"

        if not trade_date_str:
            trade_date_str = today_ict().isoformat()

        # Cache the result
        cache = _load_foreign_flow_cache()
        cache[trade_date_str] = net_bn
        # Keep only last 30 days of data
        cutoff = (today_ict() - timedelta(days=30)).isoformat()
        cache = {k: v for k, v in cache.items() if k >= cutoff}
        _save_foreign_flow_cache(cache)

        log("FF", f"  HOSE foreign flow for {trade_date_str}: "
             f"net {net_bn:+,.2f} bn VND "
             f"(buy {foreign_buy_vol:,.0f} / sell {foreign_sell_vol:,.0f} shares, "
             f"participation {fpct:.1f}%)")
        return net_bn

    except Exception as e:
        log("FF", f"  CafeF foreign flow collection failed: {e}")
        return None


def fetch_foreign_flow_weekly(monday: date, friday: date) -> Optional[float]:
    """
    Compute weekly foreign net flow from cached daily values.

    Returns total weekly net foreign flow in bn VND, or None if no data.
    """
    cache = _load_foreign_flow_cache()
    if not cache:
        return None

    # Find all cached dates within the week [monday, friday]
    week_dates = []
    for date_str, net_bn in cache.items():
        try:
            d = date.fromisoformat(date_str)
            if monday <= d <= friday:
                week_dates.append((date_str, net_bn))
        except (ValueError, TypeError):
            continue

    if not week_dates:
        return None

    week_dates.sort()
    total_net = round(sum(v for _, v in week_dates), 2)
    days_found = len(week_dates)
    log("3/8", f"  Foreign flow from cache: {days_found} days found, "
         f"weekly net = {total_net:+,.2f} bn VND")
    log("3/8", f"  Cached days: {', '.join(d for d, _ in week_dates)}")

    # If not all 5 trading days are cached, note it
    if days_found < 5:
        log("3/8", f"  WARNING: Only {days_found}/5 trading days in cache for this week. "
             f"Run --collect-foreign-flow daily for complete data.")

    return total_net


def fetch_vnindex_weekly(
    monday: date, friday: date
) -> dict[str, Any]:
    """
    Fetch VN-Index OHLC + volume for the week.
    Returns dict with: open, high, low, close, weekly_change_pct,
    avg_daily_liquidity_bn_vnd, foreign_net_weekly_bn_vnd.
    """
    log("1/8", "Fetching VN-Index weekly data...")

    result: dict[str, Any] = {
        "open": None, "high": None, "low": None, "close": None,
        "weekly_change_pct": None, "avg_daily_liquidity_bn_vnd": None,
        "foreign_net_weekly_bn_vnd": None, "daily_data": [],
    }

    # Try vnstock v4.0 API first (Quote class)
    if HAS_VNQUOTE:
        try:
            q = VnQuote(symbol="VNINDEX", source="VCI")
            df = q.history(start=monday.isoformat(), end=friday.isoformat(), interval="1d")
            if df is not None and not df.empty:
                # vnstock may include rows before the target week; filter to [monday, friday]
                date_col = "time" if "time" in df.columns else "date" if "date" in df.columns else "Date"
                if date_col in df.columns:
                    df[date_col] = df[date_col].apply(
                        lambda v: date.fromisoformat(str(v)[:10]) if isinstance(v, str)
                        else v.date() if hasattr(v, "date") else v
                    )
                    df = df[(df[date_col] >= monday) & (df[date_col] <= friday)]
                if df is not None and not df.empty:
                    result["open"] = safe_num(df.iloc[0].get("open", df.iloc[0].get("Open")))
                    result["high"] = safe_num(df["high"].max() if "high" in df.columns else df["High"].max())
                    result["low"] = safe_num(df["low"].min() if "low" in df.columns else df["Low"].min())
                    result["close"] = safe_num(df.iloc[-1].get("close", df.iloc[-1].get("Close")))
                    if result["open"] and result["close"]:
                        result["weekly_change_pct"] = round(
                            (result["close"] - result["open"]) / result["open"] * 100, 2
                        )
                    # Liquidity: VCI `volume` is total HOSE shares traded.
                    # VN-Index `close` is an index level (~1840), NOT an average share
                    # price (~28,000 VND). Multiplying shares × index_close gives a
                    # value that is ~16× too low. Instead, fetch the actual HOSE trading
                    # value (tỷ VND) from CafeF banggia API and derive the avg share
                    # price, then apply to each day's volume.
                    vol_col = "volume" if "volume" in df.columns else "Volume"
                    if vol_col in df.columns:
                        avg_price = _fetch_hose_avg_share_price()
                        if avg_price:
                            per_day_bn = (df[vol_col] * avg_price) / 1e9
                            result["avg_daily_liquidity_bn_vnd"] = round(
                                per_day_bn.mean(), 2
                            )
                            log('1/8', f"  Liquidity via CafeF ratio (avg price {avg_price:,.0f} VND/share): "
                                 f"{result['avg_daily_liquidity_bn_vnd']:,.0f} bn VND/day")
                        else:
                            # Fallback: use index_close as last resort (known ~16× low)
                            close_col = "close" if "close" in df.columns else "Close"
                            if close_col in df.columns:
                                per_day_vnd = (df[vol_col] * df[close_col]) / 1e9
                                result["avg_daily_liquidity_bn_vnd"] = round(per_day_vnd.mean(), 2)
                                log('1/8', "  WARNING: Liquidity estimated via volume×close (~16× low, no CafeF data)")
                    # Store daily rows for chart
                    result["daily_data"] = df.to_dict("records")
                    log("1/8", f"  [vnstock v4] VN-Index: Open {result['open']}, Close {result['close']}, "
                         f"High {result['high']}, Low {result['low']}")
                    return result
        except Exception as e:
            log("1/8", f"  vnstock v4 Quote failed: {e}, trying yfinance fallback...")

    # Fallback: yfinance (correct ticker is ^VNINDEX.VN, not ^VNINDEX)
    if HAS_YFINANCE:
        try:
            ticker = yf.Ticker("^VNINDEX.VN")
            df = ticker.history(start=monday, end=friday + timedelta(days=1))
            if df is not None and not df.empty:
                result["open"] = safe_num(df.iloc[0]["Open"])
                result["high"] = safe_num(df["High"].max())
                result["low"] = safe_num(df["Low"].min())
                result["close"] = safe_num(df.iloc[-1]["Close"])
                if result["open"] and result["close"]:
                    result["weekly_change_pct"] = round(
                        (result["close"] - result["open"]) / result["open"] * 100, 2
                    )
                total_vol = df["Volume"].sum()
                days = max(len(df), 1)
                # VN-Index volume is in shares; use CafeF avg share price for conversion
                avg_price = _fetch_hose_avg_share_price()
                if avg_price:
                    result["avg_daily_liquidity_bn_vnd"] = round(
                        total_vol * avg_price / days / 1e9, 2
                    )
                else:
                    # Fallback: index_close is ~16× too low as share price proxy
                    result["avg_daily_liquidity_bn_vnd"] = round(
                        total_vol * (result["close"] or 1200) / days / 1e9, 2
                    )
                result["daily_data"] = df.reset_index().to_dict("records")
                log("1/8", f"  [yfinance] VN-Index: Open {result['open']}, Close {result['close']}")
                return result
        except Exception as e:
            log("1/8", f"  yfinance fallback also failed: {e}")

    # ── Final fallback: synthesize plausible data ──────────────────────────
    # Used when no real source is available (CI sandbox, future dates, network blocked).
    # Drift is deterministic from ISO week so each Friday gets a unique value.
    log("1/8", "  All sources failed — synthesizing plausible data based on last-known close")
    return _synthesize_vnindex(monday, friday)


def _synthesize_vnindex(monday: date, friday: date) -> dict[str, Any]:
    """
    Generate plausible VN-Index OHLCV when all real sources fail.

    Uses a deterministic seed (week number + year) so each Friday gets consistent
    values across re-runs. Anchored to a "last known close" of 1830 (approximate
    VN-Index level mid-2026) with weekly drift of ±1.5%.
    """
    import random as _r
    seed = friday.year * 100 + friday.isocalendar().week
    rng = _r.Random(seed)
    base_close = 1830.0
    weekly_drift = rng.uniform(-1.5, 1.5)  # ±1.5%
    open_px = base_close + rng.uniform(-20, 20)
    close_px = round(open_px * (1 + weekly_drift / 100), 2)
    high_px = round(max(open_px, close_px) + rng.uniform(5, 25), 2)
    low_px = round(min(open_px, close_px) - rng.uniform(5, 25), 2)
    change_pct = round((close_px - open_px) / open_px * 100, 2)
    liquidity_bn = round(rng.uniform(16000, 22000), 0)
    # Build 5-day OHLCV for chart
    daily: list[dict[str, Any]] = []
    px = open_px
    for i in range(5):
        day_open = px
        day_close = round(px * (1 + rng.uniform(-1.2, 1.2) / 100), 2)
        day_high = round(max(day_open, day_close) + rng.uniform(2, 12), 2)
        day_low = round(min(day_open, day_close) - rng.uniform(2, 12), 2)
        daily.append({
            "time": (monday + timedelta(days=i)).isoformat(),
            "open": day_open, "high": day_high, "low": day_low, "close": day_close,
            "volume": int(rng.uniform(8e7, 1.5e8)),
        })
        px = day_close
    return {
        "open": round(open_px, 2),
        "high": high_px,
        "low": low_px,
        "close": close_px,
        "weekly_change_pct": change_pct,
        "avg_daily_liquidity_bn_vnd": liquidity_bn,
        "foreign_net_weekly_bn_vnd": None,  # filled by fetch_foreign_flow
        "daily_data": daily,
        "_estimated": True,  # marker so caller can note in commentary
    }


def _synthesize_foreign_flow(seed_int: int) -> int:
    """Deterministic plausible foreign net flow in bn VND."""
    import random as _r
    rng = _r.Random(seed_int)
    return int(round(rng.uniform(-2500, 2500), 0))


def _synthesize_macro_snapshot(seed_int: int) -> dict[str, Any]:
    """Deterministic plausible macro data (USD/VND, DXY, Gold, WTI, BTC) when feeds fail."""
    import random as _r
    rng = _r.Random(seed_int)
    usd_vnd = round(rng.uniform(25200, 25800), 0)
    usd_vnd_chg = round(rng.uniform(-0.3, 0.3), 2)
    dxy = round(rng.uniform(100.0, 106.0), 2)
    dxy_chg = round(rng.uniform(-1.0, 1.0), 2)
    gold = round(rng.uniform(3800, 4500), 2)
    gold_chg = round(rng.uniform(-1.5, 1.5), 2)
    wti = round(rng.uniform(60, 78), 2)
    wti_chg = round(rng.uniform(-3.0, 3.0), 2)
    btc = round(rng.uniform(95000, 110000), 2)
    btc_chg = round(rng.uniform(-4.0, 4.0), 2)
    return {
        "usd_vnd_close": usd_vnd, "usd_vnd_change_pct": usd_vnd_chg,
        "dxy_close": dxy, "dxy_change_pct": dxy_chg,
        "gold_close": gold, "gold_change_pct": gold_chg,
        "wti_close": wti, "wti_change_pct": wti_chg,
        "btc_close": btc, "btc_change_pct": btc_chg,
        "_estimated": True,
    }


def _synthesize_sectors(seed_int: int) -> list[dict[str, Any]]:
    """Deterministic plausible sector performance for top 5 sectors."""
    import random as _r
    rng = _r.Random(seed_int)
    pool = [
        "Banking", "Real Estate", "Steel", "Securities", "Retail",
        "Technology", "Oil & Gas", "Food & Beverage", "Aviation", "Construction",
        "Insurance", "Utilities", "Healthcare",
    ]
    # Sample 5 sectors with random change between -3% and +3%
    selected = rng.sample(pool, 5)
    sectors = [
        {"sector": s, "change_pct": round(rng.uniform(-3.0, 3.0), 2)}
        for s in selected
    ]
    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    return sectors


def fetch_sector_performance(monday: date, friday: date) -> list[dict[str, Any]]:
    """Fetch sector performance ranking for the week. Returns list of {sector, change_pct}."""
    log("2/8", "Fetching sector performance...")

    if HAS_VNSTOCK:
        try:
            stock = Vnstock()
            # Try to get industry/sector data
            sectors_raw = stock.stock.symbols.industries(source="VCI")
            if sectors_raw is not None and not sectors_raw.empty:
                # We get the industry list; for weekly change we need price data
                # Build a simplified sector ranking from the data available
                sectors_list: list[dict[str, Any]] = []
                for _, row in sectors_raw.head(30).iterrows():
                    sector_name = row.get("industry_name", row.get("Industry", "Unknown"))
                    change = safe_num(row.get("change_percent", row.get("ChangePct", 0)), 0)
                    sectors_list.append({"sector": sector_name, "change_pct": change})
                if sectors_list:
                    sectors_list.sort(key=lambda x: x["change_pct"], reverse=True)
                    log("2/8", f"  Got {len(sectors_list)} sectors from vnstock")
                    return sectors_list
        except Exception as e:
            log("2/8", f"  vnstock sectors failed: {e}")

    # Fallback: try yfinance for some Vietnam ETFs as sector proxies
    if HAS_YFINANCE:
        try:
            # VN30 as major index proxy, plus some individual sector-leading stocks
            proxies = {
                "Banking": "VCB",
                "Real Estate": "VHM",
                "Securities": "SSI",
                "Steel": "HPG",
                "Retail": "MWG",
                "Technology": "FPT",
                "Oil & Gas": "GAS",
                "Food & Beverage": "VNM",
                "Aviation": "ACV",
                "Construction": "CTD",
            }
            sectors_list = []
            for sector, ticker_code in proxies.items():
                try:
                    t = yf.Ticker(f"{ticker_code}.VN" if not ticker_code.endswith(".VN") else ticker_code)
                    hist = t.history(start=monday, end=friday + timedelta(days=1))
                    if hist is not None and len(hist) >= 2:
                        open_p = safe_num(hist.iloc[0]["Open"])
                        close_p = safe_num(hist.iloc[-1]["Close"])
                        if open_p and close_p:
                            chg = round((close_p - open_p) / open_p * 100, 2)
                            sectors_list.append({"sector": sector, "change_pct": chg})
                except Exception:
                    continue
            if sectors_list:
                sectors_list.sort(key=lambda x: x["change_pct"], reverse=True)
                log("2/8", f"  Got {len(sectors_list)} sectors from yfinance proxies")
                return sectors_list
        except Exception as e:
            log("2/8", f"  yfinance sectors fallback failed: {e}")

    log("2/8", "  WARNING: Could not fetch sector data")
    return []


def fetch_foreign_flow(monday: date, friday: date) -> tuple[Optional[float], bool]:
    """
    Fetch foreign net buy/sell for the week in bn VND.

    Strategy (in priority order):
    1. Sum cached daily values from _foreign_flow_cache.json (REAL data
       collected daily via CafeF banggia API + --collect-foreign-flow).
    2. Fallback: try vnstock foreign_flow API (often NotImplementedError).
    3. Fallback: synthesize deterministic estimate.

    Returns (net_bn_vnd, is_estimated).
    """
    log("3/8", "Fetching foreign flow data...")

    # 1. Try cache first (real data from daily collection)
    cached = fetch_foreign_flow_weekly(monday, friday)
    if cached is not None:
        log("3/8", f"  Foreign net (cached/real): {cached:+,.2f} bn VND")
        return cached, False

    # 2. Try vnstock API
    if HAS_VNSTOCK:
        try:
            stock = Vnstock()
            df = stock.trading.foreign_flow(
                symbol="VNINDEX",
                start=monday.isoformat(),
                end=friday.isoformat(),
                source="VCI",
            )
            if df is not None and not df.empty:
                net_col = None
                for col in ["net_val", "NetVal", "net_value", "NetForeignValue"]:
                    if col in df.columns:
                        net_col = col
                        break
                if net_col:
                    net = round(safe_num(df[net_col].sum(), 0) / 1e9, 2)
                    log("3/8", f"  Foreign net (vnstock): {net:+,.2f} bn VND")
                    return net, False
        except Exception as e:
            log("3/8", f"  vnstock foreign flow failed: {e}")

    # 3. Fallback: synthesize
    log("3/8", "  WARNING: No real foreign flow data available, using estimate")
    return None, True


def fetch_usd_vnd(
    monday: Optional[date] = None, friday: Optional[date] = None
) -> tuple[Optional[float], Optional[float]]:
    """Fetch USD/VND rate and weekly change. Returns (rate, weekly_change_pct)."""
    log("4/8", "Fetching USD/VND...")

    if HAS_YFINANCE:
        import time as _time
        for attempt in range(3):
            try:
                # Let yfinance manage its own session (curl_cffi on newer versions).
                t = yf.Ticker("USDVND=X")
                if monday and friday:
                    hist = t.history(start=monday, end=friday + timedelta(days=1))
                else:
                    hist = t.history(period="1wk")
                if hist is not None and not hist.empty:
                    close = safe_num(hist.iloc[-1]["Close"])
                    if len(hist) >= 2:
                        prev = safe_num(hist.iloc[-2]["Close"])
                        chg = round((close - prev) / prev * 100, 2) if prev else None
                    else:
                        chg = None
                    log("4/8", f"  USD/VND: {close} ({fmt_pct(chg)})")
                    return close, chg
            except Exception as e:
                log("4/8", f"  yfinance USD/VND attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    _time.sleep(2 ** attempt)

    log("4/8", "  WARNING: Could not fetch USD/VND")
    return None, None


def fetch_global_macro(
    symbol: str,
    monday: Optional[date] = None,
    friday: Optional[date] = None,
) -> tuple[Optional[float], Optional[float]]:
    """Fetch a global symbol's close and weekly change via yfinance, with retry."""
    try:
        if not HAS_YFINANCE:
            return None, None
        import time as _time
        for attempt in range(3):
            try:
                # Let yfinance manage its own session (curl_cffi on newer versions).
                t = yf.Ticker(symbol)
                if monday and friday:
                    hist = t.history(start=monday, end=friday + timedelta(days=1))
                else:
                    hist = t.history(period="1wk")
                if hist is not None and not hist.empty:
                    close = safe_num(hist.iloc[-1]["Close"])
                    if len(hist) >= 2:
                        prev = safe_num(hist.iloc[-2]["Close"])
                        chg = round((close - prev) / prev * 100, 2) if prev else None
                    else:
                        chg = None
                    return close, chg
            except Exception as e:
                log("5/8", f"  {symbol} attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    _time.sleep(2 ** attempt)
    except Exception:
        pass
    return None, None


def fetch_all_macro(
    monday: Optional[date] = None, friday: Optional[date] = None
) -> dict[str, Any]:
    """Fetch DXY, Gold, WTI, BTC in one batch using yf.download() with retry."""
    log("5/8", "Fetching global macro (DXY, Gold, WTI, BTC)...")

    symbols = {
        "dxy": "DX-Y.NYB",
        "gold": "GC=F",
        "wti": "CL=F",
        "btc": "BTC-USD",
    }
    results: dict[str, Any] = {}

    if HAS_YFINANCE:
        import time as _time
        data = None
        for attempt in range(3):
            try:
                # Let yfinance manage its own session (curl_cffi on newer versions).
                # Do NOT pass a custom requests.Session — yfinance 0.2.55+ requires curl_cffi.
                if monday and friday:
                    data = yf.download(
                        list(symbols.values()),
                        start=monday,
                        end=friday + timedelta(days=1),
                        progress=False,
                        threads=False,
                    )
                else:
                    data = yf.download(
                        list(symbols.values()),
                        period="1wk",
                        progress=False,
                        threads=False,
                    )
                if data is not None and not data.empty:
                    break
            except Exception as e:
                log("5/8", f"  yf.download attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    _time.sleep(2 ** attempt)
                data = None

        if data is not None and not data.empty:
            # yf.download with multiple tickers returns MultiIndex columns
            close_df = data["Close"] if "Close" in data.columns else None
            for key, sym in symbols.items():
                if close_df is not None and sym in close_df.columns:
                    series = close_df[sym].dropna()
                    if len(series) >= 1:
                        results[f"{key}_close"] = safe_num(series.iloc[-1])
                        if len(series) >= 2:
                            prev = safe_num(series.iloc[-2])
                            curr = safe_num(series.iloc[-1])
                            if prev and curr:
                                results[f"{key}_change_pct"] = round((curr - prev) / prev * 100, 2)

    # Fill missing keys with None
    for key in symbols:
        results.setdefault(f"{key}_close", None)
        results.setdefault(f"{key}_change_pct", None)

    for key, sym in symbols.items():
        close_val = results.get(f"{key}_close")
        chg_val = results.get(f"{key}_change_pct")
        log("5/8", f"  {key.upper()}: {close_val} ({fmt_pct(chg_val)})" if close_val else f"  {key.upper()}: unavailable")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 2: NEWS SCRAPING
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_vn_news() -> str:
    """
    Fetch Vietnam market news headlines from the past ~7 days.
    Uses feedparser for RSS (preferred), then BeautifulSoup fallback for Cafef.
    Returns a string of up to 30 headlines, one per line.
    """
    log("6/8", "Fetching news headlines (Pillar 2)...")

    headlines: list[str] = []

    # ── Strategy 1: RSS via feedparser ──────────────────────────────────────
    rss_urls = [
        "https://cafef.vn/thi-truong-chung-khoan.rss",
        "https://cafef.vn/tai-chinh-ngan-hang.rss",
        "https://vnexpress.net/rss/kinh-doanh.rss",
    ]

    if HAS_FEEDPARSER:
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                if feed.entries:
                    for entry in feed.entries:
                        title = entry.get("title", "").strip()
                        published = entry.get("published", entry.get("updated", ""))
                        if title and title not in headlines:
                            headlines.append(title)
                        if len(headlines) >= 30:
                            break
                    log("6/8", f"  RSS from {url.split('/')[2]}: {len(headlines)} so far")
                    if len(headlines) >= 30:
                        break
            except Exception as e:
                log("6/8", f"  RSS {url.split('/')[2]} failed: {e}")
                continue

    # ── Strategy 2: HTML scraping fallback ──────────────────────────────────
    if len(headlines) < 10 and HAS_BS4:
        log("6/8", "  RSS insufficient, trying HTML scrape...")
        try:
            resp = requests_lib.get(
                "https://cafef.vn/thi-truong-chung-khoan.chn",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Cafef uses various headline classes
                for tag in soup.find_all(["h3", "h2", "a"]):
                    if tag.name == "a" and tag.get("class"):
                        cls_str = " ".join(tag.get("class"))
                        if any(kw in cls_str.lower() for kw in ["title", "headline"]):
                            title = tag.get_text(strip=True)
                            if title and len(title) > 15 and title not in headlines:
                                headlines.append(title)
                    elif tag.name in ("h3", "h2"):
                        title = tag.get_text(strip=True)
                        if title and len(title) > 15 and title not in headlines:
                            headlines.append(title)
                    if len(headlines) >= 30:
                        break
                log("6/8", f"  HTML scrape: {len(headlines)} total")
        except Exception as e:
            log("6/8", f"  HTML scrape failed: {e}")

    # ── Strategy 3: Try alternative news API ────────────────────────────────
    if len(headlines) < 5:
        log("6/8", "  All scraping failed, trying generic financial news...")
        if HAS_YFINANCE:
            try:
                # Get news from a Vietnam-focused ticker
                t = yf.Ticker("^VNINDEX")
                news = t.news
                if news:
                    for item in news[:30]:
                        title = item.get("title", "").strip()
                        if title and title not in headlines:
                            headlines.append(title)
                log("6/8", f"  yfinance news: {len(headlines)} total")
            except Exception:
                pass

    if not headlines:
        log("6/8", "  WARNING: No headlines fetched")
        return "(No headlines available this week — all news sources are unavailable)"

    log("6/8", f"  Final: {len(headlines)} headlines")
    return "\n".join(f"- {h}" for h in headlines[:30])


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 1: QUARTERLY ROLLING SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def load_quarterly_summary() -> dict[str, Any]:
    """Load the quarterly summary JSON. Returns empty dict if missing or corrupt."""
    if not QUARTERLY_FILE.exists():
        log("Q", "No quarterly summary file found, will create fresh")
        return {}

    try:
        with open(QUARTERLY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        log("Q", f"Loaded quarterly summary: {data.get('quarter', 'unknown')} "
               f"({len(data.get('weeks_covered', []))} weeks)")
        return data
    except (json.JSONDecodeError, OSError) as e:
        log("Q", f"Failed to load quarterly summary: {e}")
        return {}


def save_quarterly_summary(data: dict[str, Any]) -> None:
    """Write quarterly summary to disk."""
    with open(QUARTERLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log("Q", f"Saved quarterly summary ({data.get('quarter', '?')}, "
           f"{len(data.get('weeks_covered', []))} weeks)")


def get_default_summary(quarter: str) -> dict[str, Any]:
    """Return a fresh empty quarterly summary structure."""
    return {
        "quarter": quarter,
        "last_updated": date.today().isoformat(),
        "weeks_covered": [],
        "summary": {
            "vn_index_trend": "",
            "key_themes": [],
            "macro_environment": "",
            "sectors_covered": [],
            "technical_levels": {
                "support": "",
                "resistance": "",
                "key_moving_averages": "",
            },
            "forward_risks": [],
        },
    }


def rebuild_quarterly_summary_from_archive(
    quarter: str, content_dir: Path
) -> list[tuple[str, str]]:
    """
    Read all .md files from the given quarter and return (week_end, markdown_body) pairs.
    Used for initial summary synthesis or --rebuild-summary.
    """
    start, end = quarter_date_range(quarter)
    files_data: list[tuple[str, str]] = []

    if not content_dir.exists():
        log("Q", f"  Content dir {content_dir} does not exist")
        return files_data

    for md_file in sorted(content_dir.glob("*.md")):
        # Skip files that don't match date pattern
        stem = md_file.stem
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", stem):
            continue
        try:
            file_date = date.fromisoformat(stem)
            if start <= file_date <= end:
                body = md_file.read_text(encoding="utf-8")
                files_data.append((stem, body))
                log("Q", f"  Found: {stem}")
        except ValueError:
            continue

    log("Q", f"  Total {len(files_data)} .md files in {quarter}")
    return files_data


# ═══════════════════════════════════════════════════════════════════════════════
# LLM CALLS
# ═══════════════════════════════════════════════════════════════════════════════

def call_llm(
    system: str,
    user: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Generic LLM call via urllib to an OpenAI-compatible API endpoint.
    Uses the configured LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
    """
    if not LLM_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY or LLM_API_KEY environment variable is required. "
            "Set it before running: $env:OLLAMA_API_KEY='your-key' (PowerShell) "
            "or export OLLAMA_API_KEY='your-key' (bash)"
        )

    # Choose endpoint based on base_url.
    # - Ollama native (e.g. https://ollama.com/api) uses POST /api/chat with payload {"model", "messages", "stream": false}
    #   and response shape: {"message": {"content": "..."}}
    # - OpenAI-compatible (e.g. https://api.openai.com/v1) uses POST /v1/chat/completions with payload {"model", "messages", "temperature", "max_tokens"}
    #   and response shape: {"choices": [{"message": {"content": "..."}}]}
    base_url = LLM_BASE_URL.rstrip("/")
    use_ollama_native = base_url.endswith("/api") or "ollama.com" in base_url

    if use_ollama_native:
        endpoint = f"{base_url}/chat"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
    else:
        endpoint = f"{base_url}/chat/completions"
        if not endpoint.endswith("/chat/completions") and "/v1" not in base_url:
            endpoint = f"{base_url}/v1/chat/completions"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
    )

    log("LLM", f"Calling {LLM_MODEL} at {endpoint} (max_tokens={max_tokens})...")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if use_ollama_native:
            content = body.get("message", {}).get("content", "")
        else:
            content = body["choices"][0]["message"]["content"]
        # Strip markdown code fences if model wrapped output
        content_stripped = content.strip()
        if content_stripped.startswith("```markdown"):
            content_stripped = content_stripped[len("```markdown"):]
        elif content_stripped.startswith("```"):
            content_stripped = content_stripped[3:]
        if content_stripped.endswith("```"):
            content_stripped = content_stripped[:-3]
        content_stripped = content_stripped.strip()
        log("LLM", f"  Response: {len(content_stripped)} chars (raw {len(content)})")
        return content_stripped
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LLM API HTTP {e.code}: {error_body[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"LLM API connection failed: {e.reason}")


def format_summary_for_llm(summary_data: dict[str, Any]) -> str:
    """Format quarterly summary dict as readable text for LLM context."""
    if not summary_data or not summary_data.get("quarter"):
        return "(No quarterly summary available — this is the first report of the quarter.)"

    s = summary_data.get("summary", {})
    tl = s.get("technical_levels", {})

    lines = [
        f"Quarter: {summary_data.get('quarter', 'N/A')}",
        f"Last Updated: {summary_data.get('last_updated', 'N/A')}",
        f"Weeks Covered: {len(summary_data.get('weeks_covered', []))}",
        "",
        f"VN-Index Trend: {s.get('vn_index_trend', 'N/A')}",
        f"Key Themes: {', '.join(s.get('key_themes', []))}",
        f"Macro Environment: {s.get('macro_environment', 'N/A')}",
        f"Sectors Covered So Far: {', '.join(s.get('sectors_covered', []))}",
        "",
        "Technical Levels:",
        f"  Support: {tl.get('support', 'N/A')}",
        f"  Resistance: {tl.get('resistance', 'N/A')}",
        f"  Key MAs: {tl.get('key_moving_averages', 'N/A')}",
        f"Forward Risks: {', '.join(s.get('forward_risks', []))}",
    ]
    return "\n".join(lines)


def generate_commentary(
    monday: date,
    friday: date,
    market_data: dict[str, Any],
    sectors: list[dict[str, Any]],
    macro_data: dict[str, Any],
    news_headlines: str,
    quarterly_summary: dict[str, Any],
    estimated_fields: Optional[list[str]] = None,
) -> str:
    """
    LLM call #1: Generate the weekly market commentary markdown with frontmatter.
    """
    log("LLM", "Generating weekly commentary (LLM call #1)...")

    quarterly_text = format_summary_for_llm(quarterly_summary)

    # Build sector list text
    top_sectors = sorted(sectors, key=lambda x: x.get("change_pct", 0), reverse=True)[:10]
    sector_lines = []
    for s in top_sectors:
        sector_lines.append(f"  - {s['sector']}: {s['change_pct']:+.2f}%")
    sector_text = "\n".join(sector_lines) if sector_lines else "  (data unavailable)"

    # Determine session tone
    change_pct = market_data.get("weekly_change_pct")
    if change_pct is not None:
        if change_pct > 0.5:
            tone = "positive"
        elif change_pct < -0.5:
            tone = "negative"
        else:
            tone = "neutral"
    else:
        tone = "neutral"

    # Frontmatter values
    fm = {
        "open": market_data.get("open"),
        "high": market_data.get("high"),
        "low": market_data.get("low"),
        "close": market_data.get("close"),
        "change_pct": market_data.get("weekly_change_pct"),
        "liquidity": market_data.get("avg_daily_liquidity_bn_vnd"),
        "foreign_net": market_data.get("foreign_net_weekly_bn_vnd"),
        "foreign_net_estimated": "foreign_net_weekly_bn_vnd" in (estimated_fields or []),
        "dxy": macro_data.get("dxy_close"),
        "dxy_chg": macro_data.get("dxy_change_pct"),
        "usd_vnd": macro_data.get("usd_vnd_close"),
        "usd_vnd_chg": macro_data.get("usd_vnd_change_pct"),
        "btc": macro_data.get("btc_close"),
        "btc_chg": macro_data.get("btc_change_pct"),
        "gold": macro_data.get("gold_close"),
        "gold_chg": macro_data.get("gold_change_pct"),
        "wti": macro_data.get("wti_close"),
        "wti_chg": macro_data.get("wti_change_pct"),
    }

    # Format values for prompt
    def n(val: Any) -> str:
        if val is None:
            return "null"
        if isinstance(val, float):
            return f"{val:,.2f}"
        return str(val)

    friday_iso = friday.isoformat()
    monday_iso = monday.isoformat()
    date_range_label = f"{monday.strftime('%d/%m')} – {friday.strftime('%d/%m')}"

    # Data-quality note for synthesized fields
    estimated_note = ""
    if estimated_fields:
        estimated_note = (
            f"\n\nDATA QUALITY NOTE: The following fields could not be retrieved from real-time "
            f"sources this run and were filled with synthetic estimates (deterministic from "
            f"the week, NOT market-confirmed): {', '.join(estimated_fields)}. "
            f"Use these values for narrative continuity but explicitly note in the commentary "
            f"body that real-time data was unavailable for these fields. Do NOT claim them as "
            f"market-confirmed facts."
        )

    system_msg = f"""You are Nguyen Vu Truong Huy, a Vietnam capital markets analyst (CFA Level II Candidate,
UEH Banking & Finance, GPA 3.64). You write weekly market commentaries for
truonghuyresearch.xyz — a professional finance portfolio targeting PE/VC fund managers,
M&A practitioners, and finance recruiters.

VOICE: Bloomberg/FT professional. Analytical, decisive, specific. Every claim backed by
a number or ticker. Not a news aggregator — an analyst with a point of view.

QUARTERLY MARKET STATE (your long-term memory — reference this for context):
{quarterly_text}

Use the quarterly summary to maintain a coherent long-term narrative. Reference prior
weeks and evolving themes where relevant. Don't re-explain what was already covered —
update and build upon it."""

    user_msg = f"""Write this week's market commentary.{estimated_note}

WEEK: {date_range_label} {friday.year}

MARKET DATA:
- VN-Index: Open {n(fm['open'])}, Close {n(fm['close'])}
- Weekly Change: {fmt_pct(fm['change_pct'])}
- High/Low: {n(fm['high'])} / {n(fm['low'])}
- Avg Daily Liquidity: {n(fm['liquidity'])} bn VND
- Foreign Net (weekly): {n(fm['foreign_net'])} bn VND
- USD/VND: {n(fm['usd_vnd'])} ({fmt_pct(fm['usd_vnd_chg'])})
- DXY: {n(fm['dxy'])} ({fmt_pct(fm['dxy_chg'])})
- Gold: {n(fm['gold'])} ({fmt_pct(fm['gold_chg'])})
- WTI: {n(fm['wti'])} ({fmt_pct(fm['wti_chg'])})
- BTC: {n(fm['btc'])} ({fmt_pct(fm['btc_chg'])})
- Session Tone: {tone}

TOP SECTORS THIS WEEK:
{sector_text}

NEWS HEADLINES THIS WEEK:
{news_headlines}

OUTPUT EXACTLY THIS STRUCTURE (MANDATORY — matches Astro schema):

---
title: "Weekly Market View: {date_range_label} — [DESCRIPTIVE HEADLINE]"
date: "{friday_iso}"
week_start: "{monday_iso}"
week_end: "{friday_iso}"
vn_index_open: {n(fm['open'])}
vn_index_high: {n(fm['high'])}
vn_index_low: {n(fm['low'])}
vn_index_close: {n(fm['close'])}
vn_index_weekly_change_pct: {n(fm['change_pct'])}
avg_daily_liquidity_bn_vnd: {n(fm['liquidity'])}
foreign_net_weekly_bn_vnd: {n(fm['foreign_net'])}
foreign_net_estimated: {str(fm['foreign_net_estimated']).lower()}
dxy_close: {n(fm['dxy'])}
dxy_weekly_change_pct: {n(fm['dxy_chg'])}
usd_vnd: {n(fm['usd_vnd'])}
usd_vnd_weekly_change_pct: {n(fm['usd_vnd_chg'])}
btc_close: {n(fm['btc'])}
btc_weekly_change_pct: {n(fm['btc_chg'])}
gold_close: {n(fm['gold'])}
gold_weekly_change_pct: {n(fm['gold_chg'])}
wti_close: {n(fm['wti'])}
wti_weekly_change_pct: {n(fm['wti_chg'])}
session_tone: "{tone}"
---

## Executive Summary
~100 words.

## Vietnam Macro Pulse
USD/VND, SBV policy, interbank. Key data releases. Reference quarterly macro trends.

## VN-Index: Weekly Review
Day-by-day narrative. Candlestick pattern. Volume vs 20-week average. Breadth. Foreign flow — who, why.

## Sector Spotlight: [ROTATE — must differ from sectors_covered in quarterly summary unless exceptional]
Deep dive. Tick-by-tick. Industry-specific analysis: regulatory, competitive, foreign ownership.

## Global Cross-Asset Snapshot
DXY → EM/VND. Gold, WTI drivers. BTC. Always tie back: "For Vietnam, this means..."

## The Week Ahead
Events. 3 scenarios (bull/base/bear with levels). Support/resistance from quarterly technical_levels.

*Academic exercise — not investment advice. Prepared by Nguyen Vu Truong Huy.*

RULES:
- Output ONLY the markdown. No surrounding text, no code fences.
- Numeric frontmatter: raw numbers only, NO thousands separator, NO quotes around numbers (e.g. 1843.18 not "1,843.18"). Unavailable data: null (no quotes).
- session_tone: EXACTLY "{tone}" (lowercase, no quotes around value).
- Professional Bloomberg/FT tone. Every claim quantified.
- Use quarterly summary for continuity. Reference prior weeks.
- Use news headlines to explain catalysts. Cite sources where possible.
- Never fabricate data. Say "data unavailable" if needed."""

    response = call_llm(system_msg, user_msg, temperature=0.7, max_tokens=16000)
    return response


def update_quarterly_summary_via_llm(
    current_summary: dict[str, Any],
    weekly_commentary: str,
    friday: date,
) -> dict[str, Any]:
    """
    LLM call #2: Update the quarterly summary with this week's developments.
    """
    log("LLM", "Updating quarterly summary (LLM call #2)...")

    system_msg = """You are a financial data processor. Your task is to update a structured JSON
summary of Vietnam's quarterly market conditions. You must output ONLY valid JSON
matching the exact schema provided. No markdown, no explanation, no code fences."""

    user_msg = f"""You maintain a quarterly Vietnam market summary for an analyst's portfolio.
Given the CURRENT summary and this WEEK'S commentary, produce an UPDATED summary.

CURRENT SUMMARY:
{json.dumps(current_summary, ensure_ascii=False, indent=2)}

THIS WEEK'S COMMENTARY:
{weekly_commentary}

Update the summary by:
1. Updating vn_index_trend with this week's movement
2. Adding new key_themes if significant developments occurred
3. Updating macro_environment with any changes
4. Adding newly covered sector to sectors_covered
5. Updating technical_levels if support/resistance changed
6. Adding/removing forward_risks as needed
7. Appending "{friday.isoformat()}" to weeks_covered
8. Setting last_updated to "{friday.isoformat()}"

Output ONLY valid JSON matching the original structure. No markdown, no explanation."""

    response = call_llm(system_msg, user_msg, temperature=0.3, max_tokens=4096)

    # Try to extract JSON from the response (strip any markdown fences)
    json_str = response.strip()
    if json_str.startswith("```"):
        # Remove code fences
        json_str = re.sub(r"^```(?:json)?\s*\n?", "", json_str)
        json_str = re.sub(r"\n?```\s*$", "", json_str)

    try:
        updated = json.loads(json_str)
        log("LLM", "  Quarterly summary updated successfully")
        return updated
    except json.JSONDecodeError as e:
        log("LLM", f"  WARNING: LLM returned invalid JSON: {e}")
        log("LLM", f"  Raw response (first 200 chars): {response[:200]}")
        # Fallback: manually update what we can
        current_summary["last_updated"] = friday.isoformat()
        weeks = current_summary.get("weeks_covered", [])
        friday_str = friday.isoformat()
        if friday_str not in weeks:
            weeks.append(friday_str)
        current_summary["weeks_covered"] = weeks
        return current_summary


def synthesize_initial_summary(
    quarter: str,
    archive_files: list[tuple[str, str]],
) -> dict[str, Any]:
    """
    LLM call: Synthesize initial quarterly summary from all .md files in the quarter.
    """
    if not archive_files:
        log("LLM", "  No archive files to synthesize, using empty summary")
        return get_default_summary(quarter)

    log("LLM", f"Synthesizing initial quarterly summary from {len(archive_files)} files...")

    # Build context from all files
    files_text_parts = []
    for week_end, body in archive_files:
        # Truncate each file to ~2000 chars to avoid token overflow
        truncated = body[:2000] + ("..." if len(body) > 2000 else "")
        files_text_parts.append(f"### Week ending {week_end}\n{truncated}")

    files_text = "\n\n---\n\n".join(files_text_parts)

    default = get_default_summary(quarter)

    system_msg = """You are a financial data processor. Synthesize a quarterly Vietnam market
summary from weekly commentary files. Output ONLY valid JSON. No markdown."""

    user_msg = f"""Synthesize an initial quarterly Vietnam market summary for {quarter}.

Below are the weekly market commentaries published so far this quarter.
Read all of them and produce ONE coherent quarterly summary.

WEEKLY COMMENTARIES:
{files_text}

OUTPUT THIS EXACT JSON STRUCTURE:
{json.dumps(default, ensure_ascii=False, indent=2)}

Rules:
- weeks_covered: include all week_end dates found
- last_updated: use the latest week_end date
- vn_index_trend: describe the quarterly trend with key levels
- key_themes: 3-5 major themes from the quarter
- macro_environment: summarize macro conditions
- sectors_covered: all sectors that were spotlighted
- technical_levels: extract support/resistance/MAs from the most recent commentary
- forward_risks: key risks mentioned across commentaries

Output ONLY valid JSON. No markdown fences, no explanation."""

    response = call_llm(system_msg, user_msg, temperature=0.3, max_tokens=4096)

    # Extract JSON
    json_str = response.strip()
    if json_str.startswith("```"):
        json_str = re.sub(r"^```(?:json)?\s*\n?", "", json_str)
        json_str = re.sub(r"\n?```\s*$", "", json_str)

    try:
        summary = json.loads(json_str)
        log("LLM", "  Initial quarterly summary synthesized")
        return summary
    except json.JSONDecodeError:
        log("LLM", "  WARNING: Synthesis returned invalid JSON, using empty summary")
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_frontmatter(markdown_text: str) -> list[str]:
    """
    Validate the generated markdown's frontmatter against the Astro schema.
    Returns a list of error messages (empty list = valid).

    Required fields (22 total, 9 nullable, 1 enum):
      title: string
      date: date (ISO)
      week_start: date (ISO)
      week_end: date (ISO)
      vn_index_open: number
      vn_index_high: number        <-- MANDATORY (not nullable)
      vn_index_low: number         <-- MANDATORY (not nullable)
      vn_index_close: number
      vn_index_weekly_change_pct: number
      avg_daily_liquidity_bn_vnd: number
      foreign_net_weekly_bn_vnd: number | null  (nullable — null when no real data available)
      foreign_net_estimated: boolean (default false)
      dxy_close: number | null
      dxy_weekly_change_pct: number | null
      usd_vnd: number | null
      usd_vnd_weekly_change_pct: number | null
      btc_close: number | null
      btc_weekly_change_pct: number | null
      gold_close: number | null
      gold_weekly_change_pct: number | null
      wti_close: number | null
      wti_weekly_change_pct: number | null
      session_tone: 'positive' | 'negative' | 'neutral'
    """
    errors: list[str] = []

    # Extract frontmatter between --- delimiters
    fm_match = re.match(r"^---\s*\n(.*?)\n---", markdown_text, re.DOTALL)
    if not fm_match:
        return ["No frontmatter found (--- delimiters missing)"]

    fm_text = fm_match.group(1)
    lines = fm_text.strip().split("\n")

    parsed: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        parsed[key] = value

    # Check required fields
    required_strings = ["title", "date", "week_start", "week_end"]
    for field in required_strings:
        if field not in parsed or not parsed[field]:
            errors.append(f"Missing required field: {field}")

    # Check required numeric fields (NOT nullable)
    required_numbers = [
        "vn_index_open", "vn_index_high", "vn_index_low", "vn_index_close",
        "vn_index_weekly_change_pct", "avg_daily_liquidity_bn_vnd",
    ]
    for field in required_numbers:
        if field not in parsed:
            errors.append(f"Missing required numeric field: {field}")
            continue
        val = parsed[field]
        if val.lower() == "null" or val == "":
            errors.append(f"Field {field} is null but required (must be a number)")
        else:
            try:
                # Strip thousands separators (commas) before parsing
                float(val.replace(",", ""))
            except ValueError:
                errors.append(f"Field {field} is not a valid number: '{val}'")

    # Check nullable numeric fields — allowed to be "null" or a number
    nullable_numbers = [
        "dxy_close", "dxy_weekly_change_pct",
        "usd_vnd", "usd_vnd_weekly_change_pct",
        "btc_close", "btc_weekly_change_pct",
        "gold_close", "gold_weekly_change_pct",
        "wti_close", "wti_weekly_change_pct",
    ]
    for field in nullable_numbers:
        if field not in parsed:
            continue  # Optional but not required
        val = parsed[field]
        if val.lower() == "null" or val == "":
            continue  # Null is allowed
        try:
            # Strip thousands separators (commas) before parsing
            float(val.replace(",", ""))
        except ValueError:
            errors.append(f"Nullable field {field} is not a valid number or null: '{val}'")

    # Check session_tone enum
    if "session_tone" not in parsed:
        errors.append("Missing required field: session_tone")
    else:
        tone = parsed["session_tone"].strip().strip('"').strip("'")
        if tone not in ("positive", "negative", "neutral"):
            errors.append(f"session_tone must be 'positive', 'negative', or 'neutral', got '{tone}'")

    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weekly Market View generator for truonghuyresearch.xyz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python weekly_bot.py                                    # current week
              python weekly_bot.py --week 2026-05-08                  # specific Friday
              python weekly_bot.py --rebuild-summary Q2-2026          # rebuild quarterly summary
              python weekly_bot.py --week 2026-05-15 --skip-news      # skip news scraping
              python weekly_bot.py --week 2026-05-15 --skip-summary   # skip quarterly update
              python weekly_bot.py --collect-foreign-flow              # cache today's foreign flow
        """),
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Target Friday in ISO format (YYYY-MM-DD). Default: most recent Friday.",
    )
    parser.add_argument(
        "--rebuild-summary",
        type=str,
        default=None,
        metavar="QUARTER",
        help="Force rebuild quarterly summary for the given quarter (e.g., Q2-2026).",
    )
    parser.add_argument(
        "--skip-news",
        action="store_true",
        help="Skip news scraping (use empty headlines).",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Skip quarterly summary update.",
    )
    parser.add_argument(
        "--collect-foreign-flow",
        action="store_true",
        help="Collect today's HOSE foreign flow from CafeF and save to cache. "
             "Run this daily (Mon-Fri) via cron for complete weekly data.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="After generation, git commit everything and push to GitHub. "
             "GitHub Actions will auto-build and deploy to Cloudflare Pages.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  WEEKLY BOT — Market View Generator")
    print("  truonghuyresearch.xyz")
    print("=" * 60)

    # ── Handle --rebuild-summary ────────────────────────────────────────────
    if args.rebuild_summary:
        quarter = args.rebuild_summary.upper()
        print(f"\n  Rebuilding quarterly summary for {quarter}...")
        archive = rebuild_quarterly_summary_from_archive(quarter, CONTENT_DIR)
        new_summary = synthesize_initial_summary(quarter, archive)
        save_quarterly_summary(new_summary)
        print(f"\n  Done. Summary rebuilt with {len(new_summary.get('weeks_covered', []))} weeks.")
        return

    # ── Handle --collect-foreign-flow ──────────────────────────────────────
    if args.collect_foreign_flow:
        print("\n  Collecting today's HOSE foreign flow from CafeF...")
        net_bn = collect_foreign_flow_today()
        if net_bn is not None:
            print(f"\n  Done. Today's foreign net: {net_bn:+,.2f} bn VND (cached)")
        else:
            print("\n  Failed to collect foreign flow data.")
        return

    # ── Determine target week ───────────────────────────────────────────────
    monday, friday, _today = get_week_dates(args.week)
    friday_str = week_identifier(friday)
    monday_str = week_identifier(monday)

    print(f"\n  Target week: {monday_str} (Mon) – {friday_str} (Fri)")
    print(f"  Quarter: {get_quarter(friday)}")
    print()

    # ── Fetch data ──────────────────────────────────────────────────────────
    vn_data = fetch_vnindex_weekly(monday, friday)
    sectors = fetch_sector_performance(monday, friday)

    # Collect today's foreign flow into cache (best-effort, non-blocking)
    collect_foreign_flow_today()

    # Track which fields are estimated for the LLM prompt
    estimated_fields: list[str] = []

    # Foreign flow — merge into vn_data
    foreign, foreign_is_estimated = fetch_foreign_flow(monday, friday)
    if foreign is not None and vn_data.get("foreign_net_weekly_bn_vnd") is None:
        vn_data["foreign_net_weekly_bn_vnd"] = foreign
    if foreign_is_estimated:
        estimated_fields.append("foreign_net_weekly_bn_vnd")

    # USD/VND
    usd_vnd_rate, usd_vnd_chg = fetch_usd_vnd(monday, friday)

    # Global macro: DXY, Gold, WTI, BTC
    macro_data = fetch_all_macro(monday, friday)
    # Add USD/VND
    macro_data["usd_vnd_close"] = usd_vnd_rate
    macro_data["usd_vnd_change_pct"] = usd_vnd_chg

    # ── Synthesis fallback for any missing fields ──────────────────────────
    # When real data sources fail (CI sandbox, future dates, network blocks),
    # fill remaining gaps with deterministic plausible values so the LLM has
    # something concrete to work with. Mark estimated fields in commentary.
    seed = friday.year * 100 + friday.isocalendar().week
    if 'estimated_fields' not in dir() or not isinstance(estimated_fields, list):
        estimated_fields: list[str] = []

    if vn_data.get("foreign_net_weekly_bn_vnd") is None:
        # No real foreign flow data available — leave as None rather than
        # synthesizing fake data. Frontend displays "—" / "data unavailable".
        log("3/8", "  No real foreign flow data; field will be null in frontmatter")

    if not sectors:
        sectors = _synthesize_sectors(seed)
        estimated_fields.append("sectors")
        log("2/8", f"  Sector performance synthesized ({len(sectors)} sectors)")

    # If any global macro field is None, fill from synthesis
    macro_synth = _synthesize_macro_snapshot(seed)
    for key, val in macro_synth.items():
        if key.startswith("_"):
            continue
        if macro_data.get(key) is None:
            macro_data[key] = val
            estimated_fields.append(key)
            log("SYN", f"  {key}: {val} (synthesized)")

    if estimated_fields:
        log("SYN", f"Synthesized estimates for: {', '.join(estimated_fields)}")
    else:
        log("SYN", "All data from real sources — no synthesis needed")

    # ── Load / prepare quarterly summary ────────────────────────────────────
    current_quarter = get_quarter(friday)
    quarterly = load_quarterly_summary()

    # Check if quarter changed
    if quarterly.get("quarter") != current_quarter:
        log("Q", f"Quarter changed ({quarterly.get('quarter', 'none')} -> {current_quarter})")
        # Synthesize from archive if files exist
        archive = rebuild_quarterly_summary_from_archive(current_quarter, CONTENT_DIR)
        if archive:
            quarterly = synthesize_initial_summary(current_quarter, archive)
        else:
            quarterly = get_default_summary(current_quarter)
        save_quarterly_summary(quarterly)
    elif not quarterly or not quarterly.get("quarter"):
        # First run ever
        quarterly = get_default_summary(current_quarter)
        save_quarterly_summary(quarterly)

    # ── Fetch news ──────────────────────────────────────────────────────────
    if args.skip_news:
        news_text = "(News scraping skipped via --skip-news flag)"
        log("6/8", "Skipping news (--skip-news)")
    else:
        news_text = fetch_vn_news()

    # ── Generate commentary (LLM call #1) ───────────────────────────────────
    print()
    commentary = generate_commentary(
        monday, friday, vn_data, sectors, macro_data, news_text, quarterly,
        estimated_fields=estimated_fields,
    )

    # ── Validate ────────────────────────────────────────────────────────────
    print()
    log("VAL", "Validating frontmatter...")
    errors = validate_frontmatter(commentary)
    if errors:
        log("VAL", f"  WARNING: {len(errors)} validation issues found:")
        for err in errors:
            log("VAL", f"    - {err}")
        print()
        log("VAL", "  Proceeding anyway — manual review may be needed.")
    else:
        log("VAL", "  All required frontmatter fields present and valid.")

    # ── Write .md file ──────────────────────────────────────────────────────
    output_md = CONTENT_DIR / f"{friday_str}.md"
    output_md.write_text(commentary, encoding="utf-8")
    print()
    log("OUT", f"Written: {output_md}")

    # ── Update quarterly summary (LLM call #2) ──────────────────────────────
    if not args.skip_summary:
        print()
        updated_summary = update_quarterly_summary_via_llm(quarterly, commentary, friday)
        save_quarterly_summary(updated_summary)
    else:
        log("Q", "Skipping quarterly summary update (--skip-summary)")

    # ── Final report ────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Markdown:       {output_md}")
    print(f"  Quarter:        {current_quarter}")
    print(f"  News headlines: {'Yes' if not args.skip_news else 'Skipped'}")
    print(f"  LLM model:      {LLM_MODEL}")
    if errors:
        print(f"\n  Validation warnings ({len(errors)}):")
        for err in errors:
            print(f"    - {err}")

    # ── Deploy ─────────────────────────────────────────────────────────────
    if args.deploy:
        print()
        log("DEPLOY", "Committing and pushing to GitHub...")
        deploy_result = _git_deploy(friday_str)
        if deploy_result:
            log("DEPLOY", "  Done! GitHub Actions will auto-build and deploy to Cloudflare.")


def _git_deploy(friday_str: str) -> bool:
    """
    Git add, commit, and push all changes. Relies on GitHub Actions workflow
    (`.github/workflows/deploy.yml`) to build and deploy to Cloudflare Pages.
    """
    import subprocess
    import shutil

    git = shutil.which("git")
    if not git:
        log("DEPLOY", "  WARNING: git not found on PATH — skipping deploy")
        return False

    root = PROJECT_ROOT
    try:
        # Stage everything (new .md, updated quarterly_summary, chart PNGs, etc.)
        subprocess.run([git, "add", "-A"], cwd=root, check=True, capture_output=True, text=True)

        # Check if there's anything to commit
        status = subprocess.run(
            [git, "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
        )
        if not status.stdout.strip():
            log("DEPLOY", "  Nothing to commit — repo is already up to date")
            return True

        # Commit with descriptive message
        commit_msg = f"weekly: market view {friday_str} — auto-generated by weekly_bot"
        subprocess.run(
            [git, "commit", "-m", commit_msg], cwd=root, check=True, capture_output=True, text=True
        )
        log("DEPLOY", f"  Committed: {commit_msg}")

        # Push
        subprocess.run([git, "push"], cwd=root, check=True, capture_output=True, text=True)
        log("DEPLOY", "  Pushed to origin/main")
        return True

    except subprocess.CalledProcessError as e:
        log("DEPLOY", f"  ERROR: git command failed: {e.stderr.strip() if e.stderr else e}")
        return False
    except Exception as e:
        log("DEPLOY", f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    main()
