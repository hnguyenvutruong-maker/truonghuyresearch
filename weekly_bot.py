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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

from market_memory import (
    format_market_memory_for_llm,
    load_market_memory,
    save_weekly_market_memory,
)

# ── Reconfigure stdout/stderr to UTF-8 (Windows console default is cp1252/charmap,
#    which breaks when feedparser prints Vietnamese characters) ──
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

import vn_market_data


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "market-views"
QUARTERLY_FILE = CONTENT_DIR / "_quarterly_summary.json"
FOREIGN_FLOW_CACHE = CONTENT_DIR / "_foreign_flow_cache.json"

# LLM config. Use an OpenAI-compatible endpoint by default; provider-specific
# endpoints can still be supplied through LLM_BASE_URL.
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2")

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
        # Most recent Friday. The scheduled workflow runs after market close.
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
    """Load the foreign flow cache. Supports legacy and new format."""
    if FOREIGN_FLOW_CACHE.exists():
        try:
            raw = json.loads(FOREIGN_FLOW_CACHE.read_text(encoding="utf-8"))
            # Migrate legacy format: {date: net_bn} -> {date: {net, buy, sell}}
            migrated = {}
            for k, v in raw.items():
                if isinstance(v, (int, float)):
                    migrated[k] = {"net": v, "buy": None, "sell": None}
                else:
                    migrated[k] = v
            return migrated
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


def _fetch_hsx_foreign_stock(code: str) -> Optional[dict[str, Any]]:
    """Fetch per-stock foreign flow from HSX API for current session."""
    if not HAS_BS4:
        return None
    try:
        url = f"https://api.hsx.vn/mk/api/v1/market/securities/foreign/{code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://www.hsx.vn",
            "Referer": "https://www.hsx.vn/",
        }
        resp = requests_lib.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
        data = resp.json()
        items = data.get("data", {}).get("list", [])
        if not items:
            return None
        item = items[0]
        return {
            "code": code,
            "main_buy_val": item.get("mainBuyerForeignValue", 0) or 0,
            "main_sell_val": item.get("mainSellerForeignValue", 0) or 0,
            "biglot_buy_val": item.get("bigLotBuyerForeignValue", 0) or 0,
            "biglot_sell_val": item.get("bigLotSellerForeignValue", 0) or 0,
        }
    except Exception:
        return None


def _collect_foreign_flow_hsx() -> Optional[dict[str, Any]]:
    """Collect HOSE foreign flow from HSX API (primary source).

    Aggregates per-stock foreign data across all HOSE stocks.
    Uses mainBuyerForeignValue + bigLotBuyerForeignValue for accurate totals.

    Returns dict with {net, buy, sell, source} in bn VND, or None if API fails.
    """
    if not HAS_BS4:
        log("FF", "  requests not available, skipping HSX foreign flow")
        return None

    # Step 1: Get stock list from CafeF (has all ~389 HOSE codes)
    try:
        url = "https://banggia.cafef.vn/stockhandler.ashx?center=1"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests_lib.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            log("FF", f"  CafeF stock list API returned {resp.status_code}")
            return None
        data = resp.json()
        stock_codes = [item.get("a", "") for item in data
                       if isinstance(item, dict) and item.get("a")]
        if not stock_codes:
            log("FF", "  No stock codes from CafeF")
            return None
    except Exception as e:
        log("FF", f"  CafeF stock list fetch failed: {e}")
        return None

    # Step 2: Aggregate foreign data from HSX API for all stocks (parallel)
    total_main_buy = 0.0
    total_main_sell = 0.0
    total_biglot_buy = 0.0
    total_biglot_sell = 0.0
    count = 0

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch_hsx_foreign_stock, code): code
                   for code in stock_codes}
        for future in as_completed(futures):
            result = future.result()
            if result:
                total_main_buy += result["main_buy_val"]
                total_main_sell += result["main_sell_val"]
                total_biglot_buy += result["biglot_buy_val"]
                total_biglot_sell += result["biglot_sell_val"]
                count += 1

    if count == 0:
        log("FF", "  No HSX foreign data fetched")
        return None

    # Use main board values only (consistent with official HOSE GiaoDichNN reports)
    # Note: big lot values exist in HSX API but official HOSE reports use main board only
    total_buy_vnd = total_main_buy
    total_sell_vnd = total_main_sell

    buy_bn = round(total_buy_vnd / 1e9, 2)
    sell_bn = round(total_sell_vnd / 1e9, 2)
    net_bn = round((total_buy_vnd - total_sell_vnd) / 1e9, 2)

    log("FF", f"  HSX API: {count}/{len(stock_codes)} stocks")

    return {"net": net_bn, "buy": buy_bn, "sell": sell_bn, "source": "hsx_api"}


def _collect_foreign_flow_cafef() -> Optional[dict[str, Any]]:
    """Collect HOSE foreign flow from CafeF (fallback source).

    Uses close price * foreign volume as approximation.

    Returns dict with {net, buy, sell, source} in bn VND, or None if API fails.
    """
    if not HAS_BS4:
        log("FF", "  requests not available, skipping CafeF foreign flow")
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

        foreign_buy_vnd = 0.0
        foreign_sell_vnd = 0.0
        for item in data:
            if not isinstance(item, dict):
                continue
            price_vnd = item.get("e", 0) * 1000
            fb = item.get("x", 0) or 0
            fs = item.get("y", 0) or 0
            if price_vnd > 0:
                foreign_buy_vnd += fb * price_vnd
                foreign_sell_vnd += fs * price_vnd

        buy_bn = round(foreign_buy_vnd / 1e9, 2)
        sell_bn = round(foreign_sell_vnd / 1e9, 2)
        net_bn = round((foreign_buy_vnd - foreign_sell_vnd) / 1e9, 2)

        return {"net": net_bn, "buy": buy_bn, "sell": sell_bn, "source": "cafef_approx"}
    except Exception as e:
        log("FF", f"  CafeF foreign flow collection failed: {e}")
        return None


def collect_foreign_flow_today() -> Optional[dict[str, Any]]:
    """Fetch today's HOSE foreign flow and cache it.

    Strategy (in priority order):
    1. HSX API: aggregates actual per-stock trade values (main + big lot).
    2. CafeF: uses close_price * foreign_volume as approximation.

    Returns dict with {net, buy, sell} in bn VND, or None if all sources fail.
    """
    trade_date_str = today_ict().isoformat()

    # Try to get actual date from CafeF data
    try:
        url = "https://banggia.cafef.vn/stockhandler.ashx?center=1"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests_lib.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            first_item = next((i for i in data if isinstance(i, dict)), None)
            if first_item and "Time" in first_item:
                time_str = first_item["Time"]
                parts = time_str.split()
                if len(parts) >= 2:
                    day_parts = parts[1].split("/")
                    if len(day_parts) == 3:
                        trade_date_str = f"{day_parts[2]}-{day_parts[1]}-{day_parts[0]}"
    except Exception:
        pass

    result = None

    # 1. Try HSX API (most accurate)
    log("FF", "  Trying HSX API (primary source)...")
    result = _collect_foreign_flow_hsx()

    # 2. Fallback to CafeF approximation
    if result is None:
        log("FF", "  HSX API failed, falling back to CafeF...")
        result = _collect_foreign_flow_cafef()

    if result is None:
        log("FF", "  All foreign flow sources failed")
        return None

    net_bn = result["net"]
    buy_bn = result["buy"]
    sell_bn = result["sell"]
    source = result.get("source", "unknown")

    cache = _load_foreign_flow_cache()
    cache[trade_date_str] = {"net": net_bn, "buy": buy_bn, "sell": sell_bn}
    # Keep every day: there is no historical foreign-flow API, so a pruned day
    # is gone for good (backfills and monthly notes need the full history).
    _save_foreign_flow_cache(cache)

    log("FF", f"  HOSE foreign flow for {trade_date_str} [{source}]: "
         f"net {net_bn:+,.2f} bn VND "
         f"(buy {buy_bn:,.2f} / sell {sell_bn:,.2f} bn VND)")
    return {"net": net_bn, "buy": buy_bn, "sell": sell_bn}



def fetch_foreign_flow_weekly(monday: date, friday: date) -> Optional[dict[str, Any]]:
    """
    Compute weekly foreign flow from cached daily values.

    Returns dict with {net, buy, sell} in bn VND, or None if no data.
    """
    cache = _load_foreign_flow_cache()
    if not cache:
        return None

    # Find all cached dates within the week [monday, friday]
    total_net = 0.0
    total_buy = 0.0
    total_sell = 0.0
    days_found = 0
    for date_str, entry in cache.items():
        try:
            d = date.fromisoformat(date_str)
            if monday <= d <= friday:
                if isinstance(entry, dict):
                    net_val = entry.get("net")
                    buy_val = entry.get("buy")
                    sell_val = entry.get("sell")
                else:
                    # Legacy format: just a float
                    net_val = entry
                    buy_val = None
                    sell_val = None
                if net_val is not None:
                    total_net += net_val
                    days_found += 1
                if buy_val is not None:
                    total_buy += buy_val
                if sell_val is not None:
                    total_sell += sell_val
        except (ValueError, TypeError):
            continue

    if days_found == 0:
        return None

    result = {
        "net": round(total_net, 2),
        "buy": round(total_buy, 2) if total_buy != 0 else None,
        "sell": round(total_sell, 2) if total_sell != 0 else None,
    }
    log("3/8", f"  Foreign flow from cache: {days_found} days found, "
         f"net = {result['net']:+,.2f} bn VND, "
         f"buy = {result['buy']:,.2f} / sell = {result['sell']:,.2f}" if result['buy'] else f"net = {result['net']:+,.2f} bn VND")

    # If not all 5 trading days are cached, note it
    if days_found < 5:
        log("3/8", f"  WARNING: Only {days_found}/5 trading days in cache for this week. "
             f"Run --collect-foreign-flow daily for complete data.")

    return result




def fetch_vnindex_weekly(
    monday: date, friday: date
) -> Optional[dict[str, Any]]:
    """
    Fetch VN-Index OHLC + liquidity for the week from real sources only.

    Returns dict with: open, high, low, close, weekly_change_pct,
    avg_daily_liquidity_bn_vnd, daily_data, source — or None when the index
    or its liquidity cannot be sourced. The caller must stop in that case:
    a weekly note without real index data must not be published.
    """
    log("1/8", "Fetching VN-Index weekly data...")

    rows, source = vn_market_data.fetch_vnindex_daily(monday, friday, log)
    if not rows:
        log("1/8", "  ERROR: no VN-Index source returned data for this week")
        return None

    summary = vn_market_data.summarize(rows)
    liquidity = vn_market_data.avg_daily_liquidity_bn(rows, _fetch_hose_avg_share_price())
    if liquidity is None:
        log("1/8", "  ERROR: could not derive average daily liquidity (CafeF HOSE value/volume)")
        return None

    log("1/8", f"  [{source}] VN-Index: Open {summary['open']}, Close {summary['close']}, "
         f"High {summary['high']}, Low {summary['low']}, {summary['trading_days']} sessions; "
         f"liquidity {liquidity:,.0f} bn VND/day")
    return {
        "open": summary["open"],
        "high": summary["high"],
        "low": summary["low"],
        "close": summary["close"],
        "weekly_change_pct": summary["change_pct"],
        "avg_daily_liquidity_bn_vnd": liquidity,
        "foreign_net_weekly_bn_vnd": None,
        "daily_data": rows,
        "source": source,
    }


def fetch_sector_performance(monday: date, friday: date) -> list[dict[str, Any]]:
    """Fetch sector performance ranking for the week. Returns list of {sector, change_pct}."""
    log("2/8", "Fetching sector performance...")

    # Sector-leading stocks as proxies (yfinance). Proxies, not sector indices.
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


def fetch_foreign_flow(monday: date, friday: date) -> tuple[Optional[float], Optional[float], Optional[float], bool]:
    """
    Fetch foreign buy/sell/net for the week in bn VND.

    Strategy (in priority order):
    1. Sum cached daily values from _foreign_flow_cache.json (REAL data
       collected daily via HSX / CafeF + --collect-foreign-flow).
    2. Fallback: return None values with is_estimated flag. There is no
       historical foreign-flow source; never invent these numbers.

    Returns (net_bn_vnd, buy_bn_vnd, sell_bn_vnd, is_estimated).
    buy/sell may be None even when net has a value (legacy cache format).
    """
    log("3/8", "Fetching foreign flow data...")

    # 1. Try cache first (real data from daily collection)
    cached = fetch_foreign_flow_weekly(monday, friday)
    if cached is not None:
        net_val = cached.get("net")
        buy_val = cached.get("buy")
        sell_val = cached.get("sell")
        log("3/8", f"  Foreign net (cached/real): {net_val:+,.2f} bn VND"
             f", buy={buy_val:,.2f}" if buy_val else f"  Foreign net (cached/real): {net_val:+,.2f} bn VND")
        return net_val, buy_val, sell_val, False

    # 2. Fallback: return None values
    log("3/8", "  WARNING: No real foreign flow data available")
    return None, None, None, True




def fetch_usd_vnd(
    monday: date, friday: date
) -> tuple[Optional[float], Optional[float]]:
    """Fetch USD/VND close and week-over-week change. Returns (rate, weekly_change_pct)."""
    log("4/8", "Fetching USD/VND...")

    if HAS_YFINANCE:
        import time as _time
        for attempt in range(3):
            try:
                # Let yfinance manage its own session (curl_cffi on newer versions).
                # Start a week early so the prior Friday's close is available.
                hist = yf.Ticker("USDVND=X").history(
                    start=monday - timedelta(days=7), end=friday + timedelta(days=1)
                )
                if hist is not None and not hist.empty:
                    close, chg = vn_market_data.close_and_change(hist["Close"], monday, friday)
                    if close is not None:
                        log("4/8", f"  USD/VND: {close} ({fmt_pct(chg)} w/w)")
                        return close, chg
            except Exception as e:
                log("4/8", f"  yfinance USD/VND attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    _time.sleep(2 ** attempt)

    log("4/8", "  WARNING: Could not fetch USD/VND")
    return None, None


def fetch_all_macro(monday: date, friday: date) -> dict[str, Any]:
    """Fetch DXY, Gold, WTI, BTC closes and week-over-week changes via yf.download().

    Missing values stay None: the site renders them as "—". Never fill them
    with estimates.
    """
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
                # Start a week early so the prior week's close is available.
                data = yf.download(
                    list(symbols.values()),
                    start=monday - timedelta(days=7),
                    end=friday + timedelta(days=1),
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
                    close, chg = vn_market_data.close_and_change(close_df[sym], monday, friday)
                    results[f"{key}_close"] = close
                    results[f"{key}_change_pct"] = chg

    # Fill missing keys with None
    for key in symbols:
        results.setdefault(f"{key}_close", None)
        results.setdefault(f"{key}_change_pct", None)

    for key in symbols:
        close_val = results.get(f"{key}_close")
        chg_val = results.get(f"{key}_change_pct")
        log("5/8", f"  {key.upper()}: {close_val} ({fmt_pct(chg_val)} w/w)" if close_val else f"  {key.upper()}: unavailable")

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
            "LLM_API_KEY environment variable is required. "
            "Set it before running: $env:LLM_API_KEY='your-key' (PowerShell) "
            "or export LLM_API_KEY='your-key' (bash)."
        )

    base_url = LLM_BASE_URL.rstrip("/")
    if base_url.endswith("/chat/completions"):
        endpoint = base_url
    elif base_url.endswith("/v1"):
        endpoint = f"{base_url}/chat/completions"
    else:
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
    market_memory: Optional[dict[str, Any]] = None,
    estimated_fields: Optional[list[str]] = None,
) -> str:
    """
    LLM call #1: Generate the weekly market commentary markdown with frontmatter.
    """
    log("LLM", "Generating weekly commentary (LLM call #1)...")

    quarterly_text = format_summary_for_llm(quarterly_summary)
    shared_memory_text = format_market_memory_for_llm(market_memory or {})

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
        "foreign_buy": market_data.get("foreign_buy_weekly_bn_vnd"),
        "foreign_sell": market_data.get("foreign_sell_weekly_bn_vnd"),
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

    raw = vn_market_data.yaml_scalar  # frontmatter: no thousands separators

    friday_iso = friday.isoformat()
    monday_iso = monday.isoformat()
    date_range_label = f"{monday.strftime('%d/%m')} – {friday.strftime('%d/%m')}"

    # Data-quality note for unavailable fields
    estimated_note = ""
    if estimated_fields:
        estimated_note = (
            f"\n\nDATA QUALITY NOTE: The following fields could not be retrieved from real "
            f"sources this run and are null: {', '.join(estimated_fields)}. Keep them null in "
            f"the frontmatter, do not estimate or invent values for them, and say briefly in "
            f"the body that the data was unavailable."
        )

    system_msg = f"""You are Nguyen Vu Truong Huy, a Vietnam capital markets analyst (passed Level II of the CFA Program,
UEH Banking & Finance, GPA 3.64). You write weekly market commentaries for
truonghuyresearch.xyz — a professional finance portfolio targeting PE/VC fund managers,
M&A practitioners, and finance recruiters.

VOICE: Bloomberg/FT professional. Analytical, decisive, specific. Every claim backed by
a number or ticker. Not a news aggregator — an analyst with a point of view.

QUARTERLY MARKET STATE (your long-term memory — reference this for context):
{quarterly_text}

WEEKLY / MONTHLY / QUARTERLY LINKAGE STATE:
{shared_memory_text}

Use the quarterly summary to maintain a coherent long-term narrative. Reference prior
weeks and evolving themes where relevant. Don't re-explain what was already covered —
update and build upon it. Use the linkage state to keep weekly, monthly, and quarterly
views consistent. If this week's data breaks a prior monthly or quarterly thesis,
state that change explicitly and explain why."""

    user_msg = f"""Write this week's market commentary.{estimated_note}

WEEK: {date_range_label} {friday.year}

MARKET DATA:
- VN-Index: Open {n(fm['open'])}, Close {n(fm['close'])}
- Weekly Change: {fmt_pct(fm['change_pct'])}
- High/Low: {n(fm['high'])} / {n(fm['low'])}
- Avg Daily Liquidity: {n(fm['liquidity'])} bn VND
- Foreign Net (weekly): {n(fm['foreign_net'])} bn VND
- Foreign Buy (weekly): {n(fm['foreign_buy'])} bn VND
- Foreign Sell (weekly): {n(fm['foreign_sell'])} bn VND
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
vn_index_open: {raw(fm['open'])}
vn_index_high: {raw(fm['high'])}
vn_index_low: {raw(fm['low'])}
vn_index_close: {raw(fm['close'])}
vn_index_weekly_change_pct: {raw(fm['change_pct'])}
avg_daily_liquidity_bn_vnd: {raw(fm['liquidity'])}
foreign_net_weekly_bn_vnd: {raw(fm['foreign_net'])}
foreign_buy_weekly_bn_vnd: {raw(fm['foreign_buy'])}
foreign_sell_weekly_bn_vnd: {raw(fm['foreign_sell'])}
foreign_net_estimated: {str(fm['foreign_net_estimated']).lower()}
dxy_close: {raw(fm['dxy'])}
dxy_weekly_change_pct: {raw(fm['dxy_chg'])}
usd_vnd: {raw(fm['usd_vnd'])}
usd_vnd_weekly_change_pct: {raw(fm['usd_vnd_chg'])}
btc_close: {raw(fm['btc'])}
btc_weekly_change_pct: {raw(fm['btc_chg'])}
gold_close: {raw(fm['gold'])}
gold_weekly_change_pct: {raw(fm['gold_chg'])}
wti_close: {raw(fm['wti'])}
wti_weekly_change_pct: {raw(fm['wti_chg'])}
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
- Use the linkage state to reconcile weekly, monthly, and quarterly narratives.
- Explicitly distinguish continuation themes from thesis changes.
- Use news headlines to explain catalysts. Cite sources where possible.
- Never fabricate data. Say "data unavailable" if needed.
- CRITICAL: foreign_net_weekly_bn_vnd, foreign_buy_weekly_bn_vnd, and foreign_sell_weekly_bn_vnd MUST be null when no real foreign flow data is available. Do NOT invent or estimate these values. If the provided data shows null, output null."""

    response = call_llm(system_msg, user_msg, temperature=0.7, max_tokens=16000)
    return vn_market_data.enforce_frontmatter(response, {
        "date": friday_iso,
        "week_start": monday_iso,
        "week_end": friday_iso,
        "vn_index_open": fm["open"],
        "vn_index_high": fm["high"],
        "vn_index_low": fm["low"],
        "vn_index_close": fm["close"],
        "vn_index_weekly_change_pct": fm["change_pct"],
        "avg_daily_liquidity_bn_vnd": fm["liquidity"],
        "foreign_net_weekly_bn_vnd": fm["foreign_net"],
        "foreign_buy_weekly_bn_vnd": fm["foreign_buy"],
        "foreign_sell_weekly_bn_vnd": fm["foreign_sell"],
        "foreign_net_estimated": fm["foreign_net_estimated"],
        "dxy_close": fm["dxy"],
        "dxy_weekly_change_pct": fm["dxy_chg"],
        "usd_vnd": fm["usd_vnd"],
        "usd_vnd_weekly_change_pct": fm["usd_vnd_chg"],
        "btc_close": fm["btc"],
        "btc_weekly_change_pct": fm["btc_chg"],
        "gold_close": fm["gold"],
        "gold_weekly_change_pct": fm["gold_chg"],
        "wti_close": fm["wti"],
        "wti_weekly_change_pct": fm["wti_chg"],
        "session_tone": tone,
    })


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

def _inject_daily_data(markdown: str, daily_data: list[Any]) -> str:
    """
    Inject a `vn_index_daily:` YAML block into the markdown frontmatter.
    Normalizes pandas Timestamps to ISO date strings and numpy floats to Python floats.
    Skips rows that are missing required OHLC columns. No-ops if daily_data is empty.
    """
    if not daily_data:
        return markdown

    rows: list[dict[str, Any]] = []
    for row in daily_data:
        # Determine the date
        time_val = (
            row.get("time") or row.get("date") or row.get("Date") or
            row.get("Datetime") or row.get("datetime")
        )
        if time_val is None:
            continue
        if hasattr(time_val, "isoformat"):
            time_str = str(time_val.isoformat())[:10]
        else:
            time_str = str(time_val)[:10]

        # Map column names (lowercase or yfinance capitalised)
        def _f(row: dict, *keys: str) -> float | None:
            for k in keys:
                v = row.get(k)
                if v is not None:
                    try:
                        return round(float(v), 2)
                    except (TypeError, ValueError):
                        pass
            return None

        o = _f(row, "open", "Open")
        h = _f(row, "high", "High")
        l = _f(row, "low", "Low")
        c = _f(row, "close", "Close")
        if None in (o, h, l, c):
            continue
        rows.append({"time": time_str, "open": o, "high": h, "low": l, "close": c})

    if not rows:
        return markdown

    yaml_lines = ["vn_index_daily:"]
    for r in rows:
        yaml_lines.append(
            f"  - time: \"{r['time']}\"\n"
            f"    open: {r['open']}\n"
            f"    high: {r['high']}\n"
            f"    low: {r['low']}\n"
            f"    close: {r['close']}"
        )
    daily_block = "\n".join(yaml_lines)

    # Insert before the closing --- of the frontmatter
    return re.sub(
        r"\A(\s*---\s*\n.*?)\n---",
        lambda m: m.group(1) + "\n" + daily_block + "\n---",
        markdown,
        count=1,
        flags=re.DOTALL,
    )


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
             "Run this daily via cron for complete weekly data.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="After generation, commit the generated content and push to GitHub. "
             "Vercel deploys pushes to master.",
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
        print("\n  Collecting today HOSE foreign flow...\n")
        ff_result = collect_foreign_flow_today()
        if ff_result is not None:
            print(f"\n  Done. Today's foreign net: {ff_result['net']:+,.2f} bn VND (cached)")
        else:
            print("\n  Failed to collect foreign flow data.")
            sys.exit(1)
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
    if vn_data is None:
        print("\n  ABORT: no real VN-Index data for this week — nothing was written.")
        sys.exit(1)
    sectors = fetch_sector_performance(monday, friday)

    # Collect today's foreign flow into cache (best-effort, non-blocking)
    collect_foreign_flow_today()

    # Fields with no real data this run. They stay null in frontmatter (the
    # site shows "—") and the LLM is told not to discuss them as facts.
    estimated_fields: list[str] = []

    # Foreign flow — merge into vn_data
    foreign, foreign_buy, foreign_sell, foreign_is_estimated = fetch_foreign_flow(monday, friday)
    vn_data["foreign_net_weekly_bn_vnd"] = foreign
    vn_data["foreign_buy_weekly_bn_vnd"] = foreign_buy
    vn_data["foreign_sell_weekly_bn_vnd"] = foreign_sell
    if foreign_is_estimated:
        estimated_fields.append("foreign_net_weekly_bn_vnd")

    # USD/VND
    usd_vnd_rate, usd_vnd_chg = fetch_usd_vnd(monday, friday)

    # Global macro: DXY, Gold, WTI, BTC
    macro_data = fetch_all_macro(monday, friday)
    macro_data["usd_vnd_close"] = usd_vnd_rate
    macro_data["usd_vnd_change_pct"] = usd_vnd_chg

    if not sectors:
        estimated_fields.append("sectors")
    estimated_fields += [k for k, v in macro_data.items() if v is None]

    if estimated_fields:
        log("DATA", f"Unavailable this run (left null): {', '.join(estimated_fields)}")
    else:
        log("DATA", "All fields from real sources")

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

    market_memory = load_market_memory()

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
        market_memory=market_memory,
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

    # ── Inject vn_index_daily into frontmatter ──────────────────────────────
    commentary = _inject_daily_data(commentary, vn_data.get("daily_data", []))

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
        quarterly = updated_summary
    else:
        log("Q", "Skipping quarterly summary update (--skip-summary)")

    save_weekly_market_memory(friday, commentary, quarterly)
    log("MEM", "Shared market memory updated")

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
            log("DEPLOY", "  Done! Vercel deploys pushes to master.")


def _git_deploy(friday_str: str) -> bool:
    """
    Commit the generated content and push. Vercel deploys pushes to master.
    """
    import subprocess
    import shutil

    git = shutil.which("git")
    if not git:
        log("DEPLOY", "  WARNING: git not found on PATH — skipping deploy")
        return False

    root = PROJECT_ROOT
    try:
        # Stage only bot output (the note, summaries, caches, memory) — never
        # stray files that installers or tools drop in the working tree.
        subprocess.run(
            [git, "add", "--", "src/content/market-views", "src/content/monthly-views"],
            cwd=root, check=True, capture_output=True, text=True,
        )

        # Check if there's anything staged to commit
        staged = subprocess.run(
            [git, "diff", "--cached", "--name-only"], cwd=root, check=True, capture_output=True, text=True
        )
        if not staged.stdout.strip():
            log("DEPLOY", "  Nothing to commit — repo is already up to date")
            return True

        # Commit with descriptive message
        commit_msg = f"weekly: market view {friday_str} — auto-generated by weekly_bot"
        subprocess.run(
            [git, "commit", "-m", commit_msg], cwd=root, check=True, capture_output=True, text=True
        )
        log("DEPLOY", f"  Committed: {commit_msg}")

        # Push (rebase first so a cache commit made meanwhile doesn't reject the push)
        subprocess.run([git, "pull", "--rebase", "--autostash"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run([git, "push"], cwd=root, check=True, capture_output=True, text=True)
        log("DEPLOY", "  Pushed to origin")
        return True

    except subprocess.CalledProcessError as e:
        log("DEPLOY", f"  ERROR: git command failed: {e.stderr.strip() if e.stderr else e}")
        return False
    except Exception as e:
        log("DEPLOY", f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    main()
