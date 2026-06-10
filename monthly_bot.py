#!/usr/bin/env python3
"""
monthly_bot.py — Monthly Market View generator.

Output:
  - src/content/monthly-views/{last-trading-day}.md  (Astro content collection)
  - src/content/monthly-views/_monthly_summary.json
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
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ── Reconfigure stdout/stderr to UTF-8 ──
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

# ── Optional third-party imports ──
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
    from vnstock.api.quote import Quote as VnQuote
    HAS_VNQUOTE = True
except ImportError:
    HAS_VNQUOTE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "monthly-views"
MONTHLY_SUMMARY_FILE = CONTENT_DIR / "_monthly_summary.json"
WEEKLY_CONTENT_DIR = PROJECT_ROOT / "src" / "content" / "market-views"
FOREIGN_FLOW_CACHE = WEEKLY_CONTENT_DIR / "_foreign_flow_cache.json"

LLM_API_KEY = os.getenv("OLLAMA_API_KEY") or os.getenv("LLM_API_KEY") or ""
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ollama.com/api")
LLM_MODEL = os.getenv("LLM_MODEL", "minimax-m3")

CONTENT_DIR.mkdir(parents=True, exist_ok=True)
ICT_OFFSET = timedelta(hours=7)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def today_ict() -> date:
    return (datetime.utcnow() + ICT_OFFSET).date()


def safe_num(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def log(step: str, message: str = "") -> None:
    if message:
        print(f"  [{step}] {message}")
    else:
        print(f"[{step}]")


# ═══════════════════════════════════════════════════════════════════════════════
# DATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_month_dates(month_str: Optional[str] = None) -> tuple[date, date]:
    """
    Return (first_day, last_day) for the target month.
    If month_str is provided (YYYY-MM), use that month.
    Otherwise use the most recently completed month.
    """
    today = today_ict()
    if month_str:
        year, month = month_str.split("-")
        year, month = int(year), int(month)
    else:
        # Default: previous month (if today is early in the month,
        # we want the just-completed month)
        if today.day <= 5:
            # Still early in current month → report on previous month
            if today.month == 1:
                year, month = today.year - 1, 12
            else:
                year, month = today.year, today.month - 1
        else:
            year, month = today.year, today.month

    first_day = date(year, month, 1)
    # Last day of month
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return first_day, last_day


def month_label(first: date, last: date) -> str:
    """Return 'May 2026' style label."""
    return first.strftime("%B %Y")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch_hose_avg_share_price() -> Optional[float]:
    """Fetch avg HOSE share price from CafeF banggia API (same as weekly_bot)."""
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
                val_ty = float(val_str.replace(",", ""))
                vol = float(vol_str.replace(",", ""))
                if vol > 0:
                    return val_ty * 1e9 / vol
        return None
    except Exception as e:
        log("1", f"  CafeF banggia API failed: {e}")
        return None


def _load_foreign_flow_cache() -> dict[str, Any]:
    if FOREIGN_FLOW_CACHE.exists():
        try:
            return json.loads(FOREIGN_FLOW_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def fetch_vnindex_monthly(
    first_day: date, last_day: date
) -> dict[str, Any]:
    """Fetch VN-Index OHLC + volume for the entire month."""
    log("1/7", f"Fetching VN-Index monthly data ({first_day} to {last_day})...")

    result: dict[str, Any] = {
        "open": None, "high": None, "low": None, "close": None,
        "monthly_change_pct": None, "avg_daily_liquidity_bn_vnd": None,
        "foreign_net_monthly_bn_vnd": None, "foreign_buy_monthly_bn_vnd": None, "foreign_sell_monthly_bn_vnd": None, "trading_days": 0,
        "daily_data": [],
    }

    if HAS_VNQUOTE:
        try:
            q = VnQuote(symbol="VNINDEX", source="VCI")
            df = q.history(start=first_day.isoformat(), end=last_day.isoformat(), interval="1d")
            if df is not None and not df.empty:
                import pandas as pd
                df["time"] = pd.to_datetime(df["time"])
                df = df[(df["time"] >= pd.Timestamp(first_day)) & (df["time"] <= pd.Timestamp(last_day))]

                result["open"] = safe_num(df.iloc[0].get("open", df.iloc[0].get("Open")))
                result["high"] = safe_num(df["high"].max() if "high" in df.columns else df["High"].max())
                result["low"] = safe_num(df["low"].min() if "low" in df.columns else df["Low"].min())
                result["close"] = safe_num(df.iloc[-1].get("close", df.iloc[-1].get("Close")))
                result["trading_days"] = len(df)

                if result["open"] and result["close"]:
                    result["monthly_change_pct"] = round(
                        (result["close"] - result["open"]) / result["open"] * 100, 2
                    )

                # Liquidity via CafeF ratio
                vol_col = "volume" if "volume" in df.columns else "Volume"
                if vol_col in df.columns:
                    avg_price = _fetch_hose_avg_share_price()
                    if avg_price:
                        per_day_bn = (df[vol_col] * avg_price) / 1e9
                        result["avg_daily_liquidity_bn_vnd"] = round(per_day_bn.mean(), 2)
                        log("1/7", f"  Avg daily liquidity: {result['avg_daily_liquidity_bn_vnd']:,.0f} bn VND")

                # Foreign flow from cache (with buy/sell breakdown)
                cache = _load_foreign_flow_cache()
                month_net = 0.0
                month_buy = 0.0
                month_sell = 0.0
                days_found = 0
                for date_str, entry in cache.items():
                    try:
                        d = date.fromisoformat(date_str)
                        if isinstance(entry, dict):
                            net_val = entry.get("net")
                            buy_val = entry.get("buy")
                            sell_val = entry.get("sell")
                        else:
                            # Legacy format
                            net_val = entry
                            buy_val = None
                            sell_val = None
                        if first_day <= d <= last_day:
                            if net_val is not None:
                                month_net += net_val
                                days_found += 1
                            if buy_val is not None:
                                month_buy += buy_val
                            if sell_val is not None:
                                month_sell += sell_val
                    except (ValueError, TypeError):
                        continue
                if days_found > 0:
                    result["foreign_net_monthly_bn_vnd"] = round(month_net, 2)
                    has_buy_sell = (month_buy != 0 or month_sell != 0)
                    if has_buy_sell:
                        result["foreign_buy_monthly_bn_vnd"] = round(month_buy, 2)
                        result["foreign_sell_monthly_bn_vnd"] = round(month_sell, 2)
                    log("1/7", f"  Foreign flow from cache: {days_found} days, net={month_net:+,.2f} bn VND" +
                         (f", buy={month_buy:,.2f}/sell={month_sell:,.2f}" if has_buy_sell else ""))

                result["daily_data"] = df.to_dict("records")
                log("1/7", f"  VN-Index: Open {result['open']}, Close {result['close']}, "
                     f"High {result['high']}, Low {result['low']}, Days {result['trading_days']}")
                return result
        except Exception as e:
            log("1/7", f"  vnstock failed: {e}")

    # Fallback: yfinance
    if HAS_YFINANCE:
        try:
            ticker = yf.Ticker("^VNINDEX.VN")
            df = ticker.history(start=first_day, end=last_day + timedelta(days=1))
            if df is not None and not df.empty:
                result["open"] = safe_num(df.iloc[0]["Open"])
                result["high"] = safe_num(df["High"].max())
                result["low"] = safe_num(df["Low"].min())
                result["close"] = safe_num(df.iloc[-1]["Close"])
                result["trading_days"] = len(df)
                if result["open"] and result["close"]:
                    result["monthly_change_pct"] = round(
                        (result["close"] - result["open"]) / result["open"] * 100, 2
                    )
                total_vol = df["Volume"].sum()
                days = max(len(df), 1)
                avg_price = _fetch_hose_avg_share_price()
                if avg_price:
                    result["avg_daily_liquidity_bn_vnd"] = round(total_vol * avg_price / days / 1e9, 2)
                else:
                    result["avg_daily_liquidity_bn_vnd"] = round(
                        total_vol * (result["close"] or 1200) / days / 1e9, 2
                    )
                result["daily_data"] = df.reset_index().to_dict("records")
                log("1/7", f"  [yfinance] VN-Index: Open {result['open']}, Close {result['close']}")
                return result
        except Exception as e:
            log("1/7", f"  yfinance fallback failed: {e}")

    log("1/7", "  WARNING: Could not fetch VN-Index data")
    return result


def fetch_sector_performance_monthly(
    first_day: date, last_day: date
) -> list[dict[str, Any]]:
    """Fetch sector performance for the month using yfinance proxies."""
    log("2/7", "Fetching sector performance...")

    # Vietnamese sector proxies (same as weekly_bot)
    SECTOR_PROXIES = {
        "Banking": "VCB.VN", "Real Estate": "VHM.VN", "Steel": "HPG.VN",
        "Technology": "FPT.VN", "Oil & Gas": "PLX.VN", "Securities": "SSI.VN",
        "Retail": "MWG.VN", "Construction": "HBC.VN", "Utilities": "POW.VN",
        "Aviation": "HVN.VN", "F&B": "VNM.VN",
    }

    sectors_list: list[dict[str, Any]] = []

    if HAS_YFINANCE:
        import time as _time
        for sector, ticker_str in SECTOR_PROXIES.items():
            try:
                _time.sleep(0.3)
                t = yf.Ticker(ticker_str)
                hist = t.history(start=first_day, end=last_day + timedelta(days=1))
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
        log("2/7", f"  Got {len(sectors_list)} sectors")

    return sectors_list


def fetch_week_recap(first_day: date, last_day: date) -> list[dict[str, Any]]:
    """Build a week-by-week recap for the month from VN-Index data."""
    log("3/7", "Building week recap...")

    weeks: list[dict[str, Any]] = []

    if HAS_VNQUOTE:
        try:
            q = VnQuote(symbol="VNINDEX", source="VCI")
            df = q.history(start=first_day.isoformat(), end=last_day.isoformat(), interval="1d")
            if df is not None and not df.empty:
                import pandas as pd
                df["time"] = pd.to_datetime(df["time"])
                df = df[(df["time"] >= pd.Timestamp(first_day)) & (df["time"] <= pd.Timestamp(last_day))]

                # Group by ISO week
                df["week_num"] = df["time"].dt.isocalendar().week.astype(int)
                for week_num, week_df in df.groupby("week_num"):
                    week_open = safe_num(week_df.iloc[0].get("close", week_df.iloc[0].get("Close")))
                    week_close = safe_num(week_df.iloc[-1].get("close", week_df.iloc[-1].get("Close")))
                    if week_open and week_close:
                        chg = round((week_close - week_open) / week_open * 100, 2)
                    else:
                        chg = None
                    week_start = week_df["time"].min().strftime("%d/%m")
                    week_end = week_df["time"].max().strftime("%d/%m")
                    weeks.append({
                        "label": f"{week_start} – {week_end}",
                        "change_pct": chg,
                        "trading_days": len(week_df),
                    })
        except Exception as e:
            log("3/7", f"  Week recap failed: {e}")

    if weeks:
        log("3/7", f"  {len(weeks)} weeks recap: " +
             ", ".join(f"{w['label']}={fmt_pct(w['change_pct'])}" for w in weeks))

    return weeks


def fetch_macro_monthly(
    first_day: date, last_day: date
) -> dict[str, Any]:
    """Fetch global macro data (DXY, Gold, WTI, BTC, USD/VND) for the month."""
    log("4/7", "Fetching macro data...")

    result: dict[str, Any] = {}
    if HAS_YFINANCE:
        import time as _time
        try:
            data = yf.download(
                ["DX-Y.NYB", "GC=F", "CL=F", "BTC-USD"],
                start=first_day, end=last_day + timedelta(days=1),
                group_by="ticker", auto_adjust=True, progress=False,
            )
            for ticker, key_close, key_chg in [
                ("DX-Y.NYB", "dxy_close", "dxy_monthly_change_pct"),
                ("GC=F", "gold_close", "gold_monthly_change_pct"),
                ("CL=F", "wti_close", "wti_monthly_change_pct"),
                ("BTC-USD", "btc_close", "btc_monthly_change_pct"),
            ]:
                try:
                    if data.columns.nlevels > 1:
                        sub = data[ticker]["Close"].dropna()
                    else:
                        sub = data["Close"].dropna()
                    if len(sub) >= 2:
                        result[key_close] = round(safe_num(sub.iloc[-1]), 2)
                        result[key_chg] = round((sub.iloc[-1] / sub.iloc[0] - 1) * 100, 2)
                    elif len(sub) == 1:
                        result[key_close] = round(safe_num(sub.iloc[-1]), 2)
                        result[key_chg] = None
                except Exception:
                    continue
            _time.sleep(0.5)
        except Exception as e:
            log("4/7", f"  Macro download failed: {e}")

        # USD/VND
        try:
            t = yf.Ticker("USDVND=X")
            hist = t.history(start=first_day, end=last_day + timedelta(days=1))
            if hist is not None and not hist.empty:
                close = safe_num(hist.iloc[-1]["Close"])
                result["usd_vnd"] = round(close, 2) if close else None
                if len(hist) >= 2:
                    prev = safe_num(hist.iloc[0]["Open"])
                    result["usd_vnd_monthly_change_pct"] = round(
                        (close - prev) / prev * 100, 2
                    ) if (close and prev) else None
        except Exception as e:
            log("4/7", f"  USD/VND failed: {e}")

    log("4/7", f"  Macro: DXY={result.get('dxy_close')}, Gold={result.get('gold_close')}, "
         f"BTC={result.get('btc_close')}, WTI={result.get('wti_close')}, USD/VND={result.get('usd_vnd')}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# LLM
# ═══════════════════════════════════════════════════════════════════════════════

def call_llm(system: str, user: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Call LLM via OpenAI-compatible API (same pattern as weekly_bot)."""
    if not LLM_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY or LLM_API_KEY environment variable is required.")

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
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
    else:
        endpoint = f"{base_url}/v1/chat/completions" if "/v1" not in base_url else f"{base_url}/chat/completions"
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
        endpoint, data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LLM_API_KEY}"},
    )

    log("LLM", f"Calling {LLM_MODEL} (max_tokens={max_tokens})...")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if use_ollama_native:
            content = body.get("message", {}).get("content", "")
        else:
            content = body["choices"][0]["message"]["content"]
        # Strip code fences
        content = content.strip()
        if content.startswith("```markdown"):
            content = content[len("```markdown"):]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        log("LLM", f"  Response: {len(content)} chars")
        return content
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LLM API HTTP {e.code}: {error_body[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"LLM API connection failed: {e.reason}")


# ═══════════════════════════════════════════════════════════════════════════════
# MONTHLY SUMMARY (rolling memory)
# ═══════════════════════════════════════════════════════════════════════════════

def load_monthly_summary() -> dict[str, Any]:
    if MONTHLY_SUMMARY_FILE.exists():
        try:
            return json.loads(MONTHLY_SUMMARY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_updated": "", "months_covered": [], "current_month": {}, "prior_months": []}


def save_monthly_summary(summary: dict[str, Any]) -> None:
    MONTHLY_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MONTHLY_SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def format_summary_for_llm(summary: dict[str, Any]) -> str:
    cm = summary.get("current_month", {})
    if not cm:
        return "(No prior monthly summary available — this is the first report.)"
    lines = [
        f"Prior Month: {cm.get('month_label', 'N/A')}",
        f"VN-Index Trend: {cm.get('vn_index_trend', 'N/A')}",
        f"Key Themes: {', '.join(cm.get('key_themes', [])[:5])}",
        f"Macro Regime: {cm.get('macro_regime', 'N/A')}",
        f"Foreign Flow Direction: {cm.get('foreign_flow_direction', 'N/A')}",
        f"Forward Risks: {', '.join(cm.get('forward_risks', [])[:3])}",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# COMMENTARY GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_commentary(
    first_day: date, last_day: date,
    market_data: dict[str, Any],
    sectors: list[dict[str, Any]],
    week_recap: list[dict[str, Any]],
    macro_data: dict[str, Any],
    monthly_summary: dict[str, Any],
) -> str:
    """LLM call: Generate the monthly market commentary markdown."""
    log("LLM", "Generating monthly commentary...")

    summary_text = format_summary_for_llm(monthly_summary)

    # Best/worst sectors
    best_sector = sectors[0] if sectors else None
    worst_sector = sectors[-1] if sectors else None

    # Week recap text
    recap_lines = []
    for w in week_recap:
        chg = fmt_pct(w.get("change_pct"))
        recap_lines.append(f"  - {w['label']}: {chg}")
    recap_text = "\n".join(recap_lines) if recap_lines else "  (data unavailable)"

    # Sector text
    sector_lines = []
    for s in sectors[:10]:
        sector_lines.append(f"  - {s['sector']}: {fmt_pct(s['change_pct'])}")
    sector_text = "\n".join(sector_lines) if sector_lines else "  (data unavailable)"

    # Determine session tone
    change_pct = market_data.get("monthly_change_pct")
    if change_pct is not None:
        if change_pct > 2:
            tone = "positive"
        elif change_pct < -2:
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
        "change_pct": market_data.get("monthly_change_pct"),
        "liquidity": market_data.get("avg_daily_liquidity_bn_vnd"),
        "foreign_net": market_data.get("foreign_net_monthly_bn_vnd"),
        "foreign_buy": market_data.get("foreign_buy_monthly_bn_vnd"),
        "foreign_sell": market_data.get("foreign_sell_monthly_bn_vnd"),
        "foreign_net_estimated": False,  # Only true if synthetic; cache data is real
        "trading_days": market_data.get("trading_days", 0),
        "best_sector": best_sector["sector"] if best_sector else None,
        "best_sector_chg": best_sector["change_pct"] if best_sector else None,
        "worst_sector": worst_sector["sector"] if worst_sector else None,
        "worst_sector_chg": worst_sector["change_pct"] if worst_sector else None,
        "dxy": macro_data.get("dxy_close"),
        "dxy_chg": macro_data.get("dxy_monthly_change_pct"),
        "usd_vnd": macro_data.get("usd_vnd"),
        "usd_vnd_chg": macro_data.get("usd_vnd_monthly_change_pct"),
        "btc": macro_data.get("btc_close"),
        "btc_chg": macro_data.get("btc_monthly_change_pct"),
        "gold": macro_data.get("gold_close"),
        "gold_chg": macro_data.get("gold_monthly_change_pct"),
        "wti": macro_data.get("wti_close"),
        "wti_chg": macro_data.get("wti_monthly_change_pct"),
    }

    def n(val: Any) -> str:
        if val is None:
            return "null"
        if isinstance(val, float):
            return f"{val:,.2f}"
        return str(val)

    m_label = month_label(first_day, last_day)

    system_prompt = textwrap.dedent("""\
        You are a senior capital markets analyst writing a Monthly Market View report
        for the Vietnam stock market (HOSE / VN-Index). You write in concise, data-dense
        English with a Bloomberg-terminal tone. You are factual and avoid speculation.

        CRITICAL: Your output MUST be a valid Markdown document starting with a YAML
        frontmatter block (between --- delimiters). The frontmatter must contain exactly
        these fields with these types:

        Required fields:
          title: string
          date: date (ISO, use the last trading day of the month)
          month_start: date (ISO)
          month_end: date (ISO)
          session_tone: "positive" | "negative" | "neutral"
          vn_index_open: number
          vn_index_high: number
          vn_index_low: number
          vn_index_close: number
          vn_index_monthly_change_pct: number
          avg_daily_liquidity_bn_vnd: number
          foreign_net_monthly_bn_vnd: number | null
          foreign_buy_monthly_bn_vnd: number | null  (nullable — foreign inflow in bn VND)
          foreign_sell_monthly_bn_vnd: number | null  (nullable — foreign outflow in bn VND)
          foreign_net_estimated: boolean
          trading_days: number
          best_sector: string | null
          best_sector_change_pct: number | null
          worst_sector: string | null
          worst_sector_change_pct: number | null
          dxy_close: number | null
          dxy_monthly_change_pct: number | null
          usd_vnd: number | null
          usd_vnd_monthly_change_pct: number | null
          btc_close: number | null
          btc_monthly_change_pct: number | null
          gold_close: number | null
          gold_monthly_change_pct: number | null
          wti_close: number | null
          wti_monthly_change_pct: number | null

        After the frontmatter, write these 6 markdown sections:
        1. ## Executive Summary (~150 words)
        2. ## Macro Regime — VND policy, SBV stance, inflation, credit growth
        3. ## VN-Index Monthly Review — include week-by-week recap
        4. ## Sector Rotation Map — best/worst sectors, rotation narrative
        5. ## Global Cross-Asset Synthesis — DXY, Gold, WTI, BTC monthly moves
        6. ## The Month Ahead — forward risks and catalysts

        DO NOT wrap output in code fences. Output raw markdown.
    """)

    user_prompt = textwrap.dedent(f"""\
        Generate the Monthly Market View for {m_label}.

        ## Prior Monthly Context
        {summary_text}

        ## VN-Index Data (Monthly)
        - Open: {n(fm['open'])}
        - Close: {n(fm['close'])}
        - High: {n(fm['high'])}
        - Low: {n(fm['low'])}
        - Monthly Change: {fmt_pct(fm['change_pct'])}
        - Avg Daily Liquidity: {n(fm['liquidity'])} bn VND
        - Foreign Net Monthly: {n(fm['foreign_net'])} bn VND
- Foreign Buy Monthly: {n(fm['foreign_buy'])} bn VND
- Foreign Sell Monthly: {n(fm['foreign_sell'])} bn VND
        - Trading Days: {fm['trading_days']}

        ## Week-by-Week Recap
        {recap_text}

        ## Sector Performance (Monthly)
        {sector_text}

        ## Global Macro (Monthly)
        - DXY: {n(fm['dxy'])} ({fmt_pct(fm['dxy_chg'])})
        - USD/VND: {n(fm['usd_vnd'])} ({fmt_pct(fm['usd_vnd_chg'])})
        - Gold: {n(fm['gold'])} ({fmt_pct(fm['gold_chg'])})
        - WTI: {n(fm['wti'])} ({fmt_pct(fm['wti_chg'])})
        - BTC: {n(fm['btc'])} ({fmt_pct(fm['btc_chg'])})

        ## Output Format
        Frontmatter fields (YAML between --- delimiters):
          title: "Monthly Market View: {m_label} — [DESCRIPTIVE HEADLINE]"
          date: "{last_day.isoformat()}"
          month_start: "{first_day.isoformat()}"
          month_end: "{last_day.isoformat()}"
          session_tone: "{tone}"
          vn_index_open: {n(fm['open'])}
          vn_index_high: {n(fm['high'])}
          vn_index_low: {n(fm['low'])}
          vn_index_close: {n(fm['close'])}
          vn_index_monthly_change_pct: {n(fm['change_pct'])}
          avg_daily_liquidity_bn_vnd: {n(fm['liquidity'])}
          foreign_net_monthly_bn_vnd: {n(fm['foreign_net'])}
          foreign_buy_monthly_bn_vnd: {n(fm['foreign_buy'])}
          foreign_sell_monthly_bn_vnd: {n(fm['foreign_sell'])}
          foreign_net_estimated: {str(fm['foreign_net_estimated']).lower()}
          trading_days: {fm['trading_days']}
          best_sector: {fm['best_sector'] or 'null'}
          best_sector_change_pct: {n(fm['best_sector_chg'])}
          worst_sector: {fm['worst_sector'] or 'null'}
          worst_sector_change_pct: {n(fm['worst_sector_chg'])}
          dxy_close: {n(fm['dxy'])}
          dxy_monthly_change_pct: {n(fm['dxy_chg'])}
          usd_vnd: {n(fm['usd_vnd'])}
          usd_vnd_monthly_change_pct: {n(fm['usd_vnd_chg'])}
          btc_close: {n(fm['btc'])}
          btc_monthly_change_pct: {n(fm['btc_chg'])}
          gold_close: {n(fm['gold'])}
          gold_monthly_change_pct: {n(fm['gold_chg'])}
          wti_close: {n(fm['wti'])}
          wti_monthly_change_pct: {n(fm['wti_chg'])}
        ---

        ## Executive Summary
        ~150 words.

        ## Macro Regime
        ...

        ## VN-Index Monthly Review
        Include the week-by-week recap naturally.

        ## Sector Rotation Map
        ...

        ## Global Cross-Asset Synthesis
        ...

        ## The Month Ahead
        ...
    """)

    return call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=16000)


def update_monthly_summary_via_llm(
    current_summary: dict[str, Any],
    commentary: str,
    month_label_str: str,
) -> dict[str, Any]:
    """LLM call #2: Update the monthly summary JSON."""
    log("LLM", "Updating monthly summary...")

    system = textwrap.dedent("""\
        You maintain a rolling monthly summary JSON for a Vietnam stock market analyst.
        Given the current summary and a new monthly commentary, output an updated JSON.
        Keep the same structure. Update vn_index_trend, key_themes, macro_regime,
        sector_leaders, sector_laggards, foreign_flow_direction, forward_risks.
        Output ONLY valid JSON, no markdown fences.
    """)

    current_json = json.dumps(current_summary.get("current_month", {}), indent=2, ensure_ascii=False)
    # Take last 2000 chars of commentary to stay within context
    commentary_excerpt = commentary[-2000:] if len(commentary) > 2000 else commentary

    user = f"Month: {month_label_str}\n\nCurrent summary JSON:\n{current_json}\n\nNew monthly commentary (excerpt):\n{commentary_excerpt}"

    try:
        response = call_llm(system, user, temperature=0.3, max_tokens=4096)
        # Try to parse as JSON
        new_month_data = json.loads(response)
        updated = {
            "last_updated": month_label_str,
            "months_covered": list(set(current_summary.get("months_covered", []) + [month_label_str])),
            "current_month": new_month_data,
            "prior_months": [current_summary.get("current_month", {})] + current_summary.get("prior_months", [])[:2],
        }
        return updated
    except Exception as e:
        log("LLM", f"  Summary update failed ({e}), doing manual update")
        cm = current_summary.get("current_month", {})
        updated = {
            "last_updated": month_label_str,
            "months_covered": list(set(current_summary.get("months_covered", []) + [month_label_str])),
            "current_month": cm,
            "prior_months": [cm] + current_summary.get("prior_months", [])[:2],
        }
        return updated


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_frontmatter(markdown_text: str) -> list[str]:
    """Validate YAML frontmatter against expected schema."""
    errors: list[str] = []
    fm_match = re.search(r"^---\s*\n(.*?)\n---", markdown_text, re.DOTALL)
    if not fm_match:
        errors.append("No YAML frontmatter found (must start with ---)")
        return errors

    fm_text = fm_match.group(1)
    parsed: dict[str, str] = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            parsed[key.strip()] = val.strip()

    required_strings = ["title", "date", "month_start", "month_end"]
    for field in required_strings:
        if field not in parsed or not parsed[field]:
            errors.append(f"Missing required string field: {field}")

    required_numbers = [
        "vn_index_open", "vn_index_high", "vn_index_low", "vn_index_close",
        "vn_index_monthly_change_pct", "avg_daily_liquidity_bn_vnd", "trading_days",
    ]
    for field in required_numbers:
        if field not in parsed:
            errors.append(f"Missing required numeric field: {field}")
            continue
        val = parsed[field]
        if val.lower() == "null" or val == "":
            errors.append(f"Field {field} is null but required")
        else:
            try:
                float(val.replace(",", ""))
            except ValueError:
                errors.append(f"Field {field} is not a valid number: {val}")

    if "session_tone" in parsed:
        if parsed["session_tone"].strip('"') not in ("positive", "negative", "neutral"):
            errors.append(f"Invalid session_tone: {parsed['session_tone']}")
    else:
        errors.append("Missing session_tone")

    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monthly Market View generator for truonghuyresearch.xyz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python monthly_bot.py                          # previous month
              python monthly_bot.py --month 2026-05          # specific month
              python monthly_bot.py --skip-summary           # skip monthly summary update
        """),
    )
    parser.add_argument("--month", type=str, default=None, help="Target month (YYYY-MM). Default: previous month.")
    parser.add_argument("--skip-summary", action="store_true", help="Skip monthly summary update.")
    args = parser.parse_args()

    first_day, last_day = get_month_dates(args.month)
    m_label = month_label(first_day, last_day)

    print("=" * 60)
    print("  MONTHLY BOT — Market View Generator")
    print("  truonghuyresearch.xyz")
    print("=" * 60)
    print(f"\n  Target month: {m_label}")
    print(f"  Date range: {first_day} – {last_day}")
    print()

    # ── Fetch data ──
    market_data = fetch_vnindex_monthly(first_day, last_day)
    sectors = fetch_sector_performance_monthly(first_day, last_day)
    week_recap = fetch_week_recap(first_day, last_day)
    macro_data = fetch_macro_monthly(first_day, last_day)

    # ── Load monthly summary ──
    monthly_summary = load_monthly_summary()

    # ── Generate commentary ──
    print()
    commentary = generate_commentary(
        first_day, last_day, market_data, sectors, week_recap, macro_data, monthly_summary,
    )

    # ── Validate ──
    print()
    errors = validate_frontmatter(commentary)
    if errors:
        log("VAL", f"  WARNING: {len(errors)} validation issues:")
        for err in errors:
            log("VAL", f"    - {err}")
    else:
        log("VAL", "  Frontmatter valid ✓")

    # ── Write .md file ──
    output_path = CONTENT_DIR / f"{last_day.isoformat()}.md"
    output_path.write_text(commentary, encoding="utf-8")
    log("OUT", f"  Written: {output_path}")

    # ── Update monthly summary ──
    if not args.skip_summary:
        print()
        updated = update_monthly_summary_via_llm(monthly_summary, commentary, m_label)
        save_monthly_summary(updated)
        log("SUM", f"  Monthly summary updated for {m_label}")

    print()
    print("=" * 60)
    print(f"  DONE — {m_label} monthly view generated")
    print("=" * 60)


if __name__ == "__main__":
    main()