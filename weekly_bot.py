#!/usr/bin/env python3
"""
weekly_bot.py — Weekly Market View generator (Vietnam focus).

Fetches VN-Index weekly OHLCV + sectors + foreign flow via vnstock,
global cross-asset weekly closes via yfinance, crypto via CoinGecko,
generates Bloomberg-dark matplotlib charts, and calls MiniMax M3 via
Ollama Cloud API to write a markdown post that matches the Astro
content collection schema in src/content/config.ts.

Usage:
    python weekly_bot.py                        # most recent completed week (ICT)
    python weekly_bot.py --week 2026-06-05      # week ending Friday 2026-06-05
    python weekly_bot.py --charts-only          # regenerate charts only (skip LLM)
    python weekly_bot.py --skip-charts          # skip chart generation (LLM only)

Environment:
    MINIMAX_API_KEY  — Ollama Cloud API key (required, also accepts LLM_API_KEY)
    LLM_BASE_URL     — API base URL (default: https://ollama.com/api)
    LLM_MODEL        — Model name (default: minimax-m3)
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
CONTENT_DIR = REPO_ROOT / "src" / "content" / "market-views"
CHARTS_DIR = REPO_ROOT / "public" / "charts"

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://ollama.com/api")
LLM_MODEL = os.environ.get("LLM_MODEL", "minimax-m3")
ICT = timezone(timedelta(hours=7))  # UTC+7

# Bloomberg-dark theme tokens
BG_COLOR = "#0d1117"
GRID_COLOR = "#30363d"
TEXT_COLOR = "#e6edf3"
UP_COLOR = "#84e588"
DOWN_COLOR = "#ffb4ab"
AMBER = "#f0a500"


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def get_week_dates(friday_str: str | None = None) -> tuple[str, str]:
    """Return (monday_str, friday_str) for the week that contains or ends on
    the given Friday in ICT. If friday_str is None, use the most recent
    completed Friday in ICT.
    """
    if friday_str:
        friday = datetime.strptime(friday_str, "%Y-%m-%d").replace(tzinfo=ICT)
    else:
        now_ict = datetime.now(ICT)
        # weekday(): Mon=0, Sun=6. Find last Friday (including today if Friday).
        days_since_fri = (now_ict.weekday() - 4) % 7
        if days_since_fri == 0 and now_ict.weekday() != 4:
            # Today is not Friday — go back to last completed Friday.
            days_since_fri = 7
        friday = now_ict - timedelta(days=days_since_fri)
        # If today is Friday and market has not closed (after 15:00 ICT),
        # treat the previous Friday as the "completed" week.
        if friday.date() == now_ict.date() and now_ict.weekday() == 4 and now_ict.hour < 16:
            friday = friday - timedelta(days=7)
    monday = friday - timedelta(days=4)
    return monday.strftime("%Y-%m-%d"), friday.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Data fetching — VN-Index, sectors, foreign flow
# ---------------------------------------------------------------------------

def fetch_vnindex_weekly(monday: str, friday: str) -> dict:
    """Fetch weekly OHLCV + change + average daily liquidity for VN-Index."""
    result: dict = {
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "weekly_change_pts": None,
        "weekly_change_pct": None,
        "avg_daily_liquidity_bn_vnd": None,
        "estimated": False,
    }
    try:
        from vnstock import Market  # type: ignore
        mkt = Market()
        # Fetch a wider window to be safe (handles holidays/weekends).
        start = (datetime.strptime(monday, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
        df = mkt.index("VNINDEX").ohlcv(start=start, end=friday)
        if df is None or df.empty:
            print(f"  [warn] vnstock returned empty OHLCV for {monday}..{friday}")
            return result
        # Restrict to Mon..Fri window
        df = df[(df.index >= monday) & (df.index <= friday)] if hasattr(df.index, "dtype") else df
        if df.empty:
            print(f"  [warn] no rows within Mon-Fri window after filter")
            return result
        # vnstock index: open, high, low, close, volume (some versions include 'value' / 'total_match_vol')
        first = df.iloc[0]
        last = df.iloc[-1]
        result["open"] = round(float(first["open"]), 2)
        result["high"] = round(float(df["high"].max()), 2)
        result["low"] = round(float(df["low"].min()), 2)
        result["close"] = round(float(last["close"]), 2)
        result["weekly_change_pts"] = round(result["close"] - result["open"], 2)
        result["weekly_change_pct"] = round((result["close"] - result["open"]) / result["open"] * 100, 2)
        # Liquidity: prefer 'value' (VND), fallback to volume * close (less precise)
        if "value" in df.columns:
            avg_value = float(df["value"].mean())
            result["avg_daily_liquidity_bn_vnd"] = round(avg_value / 1e9, 0)
        elif "volume" in df.columns:
            avg_vol = float(df["volume"].mean())
            result["avg_daily_liquidity_bn_vnd"] = round(avg_vol * result["close"] / 1e9, 0)
        print(f"  [ok] vnstock weekly: O={result['open']} H={result['high']} L={result['low']} C={result['close']} ({result['weekly_change_pct']:+.2f}%)")
        return result
    except Exception as e:
        print(f"  [warn] vnstock weekly fetch failed: {e}")
        result["estimated"] = True
        return result


def fetch_vnindex_daily_for_chart(monday: str, friday: str) -> "object | None":
    """Fetch ~30 days of daily OHLCV ending on Friday, used only for charting
    (candlestick + MA20 + volume). Returns a pandas DataFrame or None.
    """
    try:
        from vnstock import Market  # type: ignore
        mkt = Market()
        # Need at least 20 sessions before Friday for MA20.
        lookback_start = (datetime.strptime(monday, "%Y-%m-%d") - timedelta(days=45)).strftime("%Y-%m-%d")
        df = mkt.index("VNINDEX").ohlcv(start=lookback_start, end=friday)
        if df is None or df.empty:
            return None
        return df
    except Exception as e:
        print(f"  [warn] daily chart data fetch failed: {e}")
        return None


def fetch_sector_performance(monday: str, friday: str) -> list[dict] | None:
    """Fetch top 5 sectors by % change over the week. Returns list of
    {'name': str, 'change_pct': float} or None on failure.
    """
    try:
        from vnstock import Sector  # type: ignore
        sec = Sector()
        # Try a few common method names (vnstock API varies by version).
        df = None
        for method_name in ("overview", "valuation", "indices", "listings"):
            if hasattr(sec, method_name):
                try:
                    fn = getattr(sec, method_name)
                    df = fn() if method_name != "valuation" else fn(method="trailing_pe")
                    if df is not None and not df.empty:
                        break
                except Exception:
                    continue
        if df is None or df.empty:
            return None
        # Try to find a % change column; if not present, return raw rows.
        pct_col = None
        for cand in ("change_pct", "percent_change", "change_1w_pct", "pct_change", "change", "weekly_change_pct"):
            for col in df.columns:
                if col.lower() == cand:
                    pct_col = col
                    break
            if pct_col:
                break
        if pct_col is None:
            return None
        name_col = next((c for c in ("name", "symbol", "icb_name", "sector_name") if c in df.columns), df.columns[0])
        top = df[[name_col, pct_col]].copy()
        top[pct_col] = pd_to_numeric(top[pct_col])
        top = top.dropna(subset=[pct_col]).sort_values(pct_col, ascending=False).head(5)
        return [
            {"name": str(row[name_col]).strip(), "change_pct": round(float(row[pct_col]), 2)}
            for _, row in top.iterrows()
        ]
    except Exception as e:
        print(f"  [warn] sector performance fetch failed: {e}")
        return None


def pd_to_numeric(series):
    """Local helper: coerce a series to numeric without importing pandas at top."""
    try:
        import pandas as pd  # type: ignore
        return pd.to_numeric(series, errors="coerce")
    except Exception:
        return series


def fetch_foreign_flow_weekly(monday: str, friday: str) -> float | None:
    """Sum of daily foreign net flow over the week, in billion VND.
    Positive = net buying. None on failure.
    """
    try:
        from vnstock import Trading  # type: ignore
        t = Trading(source="VCI")
        # price_board returns latest snapshot only; sum is approximated by snapshot.
        df = t.price_board(symbols_list=["VNINDEX"])
        if df is None or df.empty:
            return None
        row = df.iloc[0]
        for col in ("foreign_net_value", "fr_net_val", "foreign_buy_value", "fr_buy_val"):
            if col in df.columns:
                val = pd_to_numeric(df[col])
                if col.startswith("foreign_buy") or col.startswith("fr_buy"):
                    sell_col = col.replace("buy", "sell")
                    if sell_col in df.columns:
                        net = float(val.iloc[0]) - float(pd_to_numeric(df[sell_col]).iloc[0])
                        return round(net / 1e9, 0)
                else:
                    return round(float(val.iloc[0]) / 1e9, 0)
        return None
    except Exception as e:
        print(f"  [warn] foreign flow fetch failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Data fetching — Vietnam macro
# ---------------------------------------------------------------------------

def fetch_usd_vnd() -> tuple[float | None, float | None]:
    """Latest USD/VND rate and ~weekly % change. Returns (rate, weekly_change_pct)."""
    # Try vnstock Macro first
    try:
        from vnstock import Macro  # type: ignore
        m = Macro()
        if hasattr(m, "exchange_rate"):
            df = m.exchange_rate(start_date=(datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"))
            if df is not None and len(df) >= 2:
                df = df.sort_index()
                rate = float(df.iloc[-1].iloc[0]) if hasattr(df, "iloc") else None
                if rate is None and "value" in df.columns:
                    rate = float(df["value"].iloc[-1])
                # Compute weekly change
                first_close = float(df.iloc[0].iloc[0]) if "value" not in df.columns else float(df["value"].iloc[0])
                pct = round((rate - first_close) / first_close * 100, 2)
                return round(rate, 0), pct
    except Exception as e:
        print(f"  [warn] vnstock Macro USD/VND failed: {e}")
    # Fallback: yfinance USDVND=X
    try:
        import yfinance as yf  # type: ignore
        t = yf.Ticker("VND=X")
        h = t.history(period="14d")
        if h is not None and len(h) >= 2:
            rate = float(h["Close"].iloc[-1])
            pct = round((rate - float(h["Close"].iloc[0])) / float(h["Close"].iloc[0]) * 100, 2)
            return round(rate, 0), pct
    except Exception as e:
        print(f"  [warn] yfinance USD/VND failed: {e}")
    return None, None


def fetch_interbank_rate() -> float | None:
    """Overnight interbank rate (%). None if unavailable."""
    try:
        from vnstock import Macro  # type: ignore
        m = Macro()
        if hasattr(m, "interbank_rate"):
            df = m.interbank_rate()
            if df is not None and not df.empty:
                # Take the latest non-null value
                return float(df.iloc[-1].iloc[0])
    except Exception as e:
        print(f"  [warn] interbank rate fetch failed: {e}")
    return None


def fetch_sbv_omo() -> dict | None:
    """SBV OMO operations — net injection/withdrawal in VND billions.
    Returns {'net_bn_vnd': float, 'available': bool}.
    """
    try:
        from vnstock import Macro  # type: ignore
        m = Macro()
        if hasattr(m, "sbv_omo"):
            df = m.sbv_omo()
            if df is not None and not df.empty:
                net = float(df.iloc[-1].iloc[0])  # depends on vnstock schema
                return {"net_bn_vnd": round(net / 1e9, 0), "available": True}
    except Exception as e:
        print(f"  [warn] SBV OMO fetch failed: {e}")
    return {"net_bn_vnd": None, "available": False}


# ---------------------------------------------------------------------------
# Data fetching — global cross-asset (yfinance)
# ---------------------------------------------------------------------------

YF_TICKERS = {
    "dxy": "DX-Y.NYB",
    "gold": "GC=F",
    "wti": "CL=F",
}


def fetch_global_markets(monday: str, friday: str) -> dict:
    """Fetch weekly close + change % for DXY, Gold, WTI via yfinance."""
    out = {"dxy_close": None, "dxy_weekly_change_pct": None,
           "gold_close": None, "gold_weekly_change_pct": None,
           "wti_close": None, "wti_weekly_change_pct": None}
    try:
        import yfinance as yf  # type: ignore
    except Exception as e:
        print(f"  [warn] yfinance not installed: {e}")
        return out
    for key, symbol in YF_TICKERS.items():
        try:
            t = yf.Ticker(symbol)
            h = t.history(start=monday, end=(datetime.strptime(friday, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"))
            if h is None or h.empty:
                print(f"  [warn] yfinance {symbol}: no data")
                continue
            close = float(h["Close"].iloc[-1])
            first = float(h["Close"].iloc[0])
            pct = round((close - first) / first * 100, 2) if first else None
            out[f"{key}_close"] = round(close, 2)
            out[f"{key}_weekly_change_pct"] = pct
        except Exception as e:
            print(f"  [warn] yfinance {symbol} failed: {e}")
    return out


# ---------------------------------------------------------------------------
# Data fetching — crypto (CoinGecko free API)
# ---------------------------------------------------------------------------

def fetch_crypto_weekly(monday: str, friday: str) -> dict:
    """Fetch BTC/ETH weekly close + change % via CoinGecko market_chart."""
    out = {"btc_close": None, "btc_weekly_change_pct": None,
           "eth_close": None, "eth_weekly_change_pct": None}
    for coin, key in (("bitcoin", "btc"), ("ethereum", "eth")):
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=10&interval=daily"
            req = urllib.request.Request(url, headers={"User-Agent": "weekly-bot/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            prices = data.get("prices", [])
            if not prices:
                print(f"  [warn] CoinGecko {coin}: empty")
                continue
            # Filter to the Mon-Fri window
            monday_ts = datetime.strptime(monday, "%Y-%m-%d").timestamp() * 1000
            friday_ts = (datetime.strptime(friday, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000
            windowed = [p for p in prices if p[0] >= monday_ts and p[0] < friday_ts]
            if not windowed:
                windowed = prices  # fall back to last 10 days
            first = windowed[0][1]
            last = windowed[-1][1]
            pct = round((last - first) / first * 100, 2) if first else None
            out[f"{key}_close"] = round(last, 2)
            out[f"{key}_weekly_change_pct"] = pct
            time.sleep(1.2)  # CoinGecko free-tier rate limit
        except Exception as e:
            print(f"  [warn] CoinGecko {coin} failed: {e}")
    return out


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------

def _setup_dark_axes(ax):
    """Apply Bloomberg-dark theme to a matplotlib axes."""
    ax.set_facecolor(BG_COLOR)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_COLOR, which="both", labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(AMBER)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)


def _chart_vnindex_weekly(daily_df, date_str: str) -> str | None:
    """5-day candlestick + volume + MA20 chart. Returns file path or None."""
    if daily_df is None or len(daily_df) < 5:
        return None
    try:
        import matplotlib  # type: ignore
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
        from matplotlib.patches import Rectangle  # type: ignore

        # Trim to last 30 days for visual density
        df = daily_df.tail(30).copy()
        # Ensure date index
        if not hasattr(df.index, "day") and "date" in df.columns:
            df.index = df["date"]
        df = df.dropna(subset=["open", "high", "low", "close"])
        if df.empty:
            return None
        df["MA20"] = df["close"].rolling(20).mean()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                         gridspec_kw={"height_ratios": [3, 1]},
                                         sharex=True, facecolor=BG_COLOR)
        # Candlesticks
        width = 0.6
        for i, (dt, row) in enumerate(df.iterrows()):
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]
            color = UP_COLOR if c >= o else DOWN_COLOR
            # Wick
            ax1.plot([i, i], [l, h], color=color, linewidth=1)
            # Body
            body_low = min(o, c)
            body_h = max(abs(c - o), (h - l) * 0.005)
            rect = Rectangle((i - width / 2, body_low), width, body_h,
                             facecolor=color, edgecolor=color, linewidth=1)
            ax1.add_patch(rect)
        ax1.plot(range(len(df)), df["MA20"], color=AMBER, linewidth=1.5, label="MA20")
        ax1.set_title(f"VN-Index Weekly — {date_str}", fontsize=14, color=AMBER, pad=12)
        ax1.set_ylabel("Index level", color=TEXT_COLOR, fontsize=10)
        ax1.legend(loc="upper left", facecolor=BG_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)
        _setup_dark_axes(ax1)

        # Volume bars
        colors = [UP_COLOR if df["close"].iloc[i] >= df["open"].iloc[i] else DOWN_COLOR
                  for i in range(len(df))]
        ax2.bar(range(len(df)), df["volume"] / 1e6, color=colors, width=0.6)
        ax2.set_ylabel("Volume (M)", color=TEXT_COLOR, fontsize=10)
        _setup_dark_axes(ax2)

        # X labels: show date for every ~5 bars
        step = max(1, len(df) // 6)
        ax2.set_xticks(range(0, len(df), step))
        ax2.set_xticklabels(
            [df.index[i].strftime("%d %b") if hasattr(df.index[i], "strftime") else str(df.index[i])
             for i in range(0, len(df), step)],
            rotation=0, color=TEXT_COLOR, fontsize=9
        )

        plt.tight_layout()
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        path = CHARTS_DIR / f"vnindex_weekly_{date_str}.png"
        fig.savefig(path, dpi=130, facecolor=BG_COLOR)
        plt.close(fig)
        print(f"  [ok] chart: {path.name}")
        return str(path)
    except Exception as e:
        print(f"  [warn] vnindex chart generation failed: {e}")
        return None


def _chart_sector_performance(sectors: list[dict] | None, date_str: str) -> str | None:
    """Horizontal bar chart for top 5 sector weekly % change."""
    if not sectors:
        return None
    try:
        import matplotlib  # type: ignore
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore

        names = [s["name"] for s in sectors][::-1]
        vals = [s["change_pct"] for s in sectors][::-1]
        colors = [UP_COLOR if v >= 0 else DOWN_COLOR for v in vals]

        fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
        bars = ax.barh(names, vals, color=colors, edgecolor=GRID_COLOR)
        ax.axvline(0, color=GRID_COLOR, linewidth=0.8)
        ax.set_title(f"Top 5 Sectors — Week of {date_str}", fontsize=14, color=AMBER, pad=12)
        ax.set_xlabel("Weekly % change", color=TEXT_COLOR, fontsize=10)
        for bar, v in zip(bars, vals):
            ax.text(v + (0.05 if v >= 0 else -0.05), bar.get_y() + bar.get_height() / 2,
                    f"{v:+.2f}%", va="center",
                    ha="left" if v >= 0 else "right",
                    color=TEXT_COLOR, fontsize=10)
        _setup_dark_axes(ax)
        plt.tight_layout()
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        path = CHARTS_DIR / f"sector_performance_{date_str}.png"
        fig.savefig(path, dpi=130, facecolor=BG_COLOR)
        plt.close(fig)
        print(f"  [ok] chart: {path.name}")
        return str(path)
    except Exception as e:
        print(f"  [warn] sector chart generation failed: {e}")
        return None


def generate_charts(week_data: dict, date_str: str) -> list[str]:
    """Generate all weekly charts. Returns list of file paths (web-friendly, e.g. /charts/...)."""
    paths: list[str] = []
    p1 = _chart_vnindex_weekly(week_data.get("_daily_df"), date_str)
    if p1:
        paths.append("/charts/" + Path(p1).name)
    p2 = _chart_sector_performance(week_data.get("sectors"), date_str)
    if p2:
        paths.append("/charts/" + Path(p2).name)
    return paths


# ---------------------------------------------------------------------------
# LLM prompt + call
# ---------------------------------------------------------------------------

def _tone_hint(change_pct: float | None) -> str:
    if change_pct is None:
        return "neutral"
    if change_pct > 0.5:
        return "positive"
    if change_pct < -0.5:
        return "negative"
    return "neutral"


def _fmt(v, suffix: str = "") -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.2f}{suffix}"
    return f"{v}{suffix}"


def build_prompt(week_data: dict, monday: str, friday: str) -> str:
    title_date = f"{datetime.strptime(monday, '%Y-%m-%d').strftime('%b %-d')} – {datetime.strptime(friday, '%Y-%m-%d').strftime('%b %-d, %Y')}"

    vn = week_data["vnindex"]
    macro = week_data["macro"]
    global_m = week_data["global"]
    crypto = week_data["crypto"]
    sectors = week_data.get("sectors") or []
    tone_hint = _tone_hint(vn.get("weekly_change_pct"))

    return f"""You are a senior Vietnam capital markets analyst writing a Weekly Market View
for a professional finance portfolio (target reader: PE/VC, M&A, fund management
professionals). Tone must be Bloomberg/Financial Times — institutional, analytical,
quantified. NOT hype, NOT clickbait, NOT bloggy.

WEEK: {title_date}

VN-INDEX (vnstock):
- Open: {vn.get('open')}
- High: {vn.get('high')}
- Low: {vn.get('low')}
- Close: {vn.get('close')}
- Weekly change: {_fmt(vn.get('weekly_change_pct'), '%')} ({_fmt(vn.get('weekly_change_pts'), ' pts')})
- Avg daily liquidity: {_fmt(vn.get('avg_daily_liquidity_bn_vnd'))} Bn VND

TOP 5 SECTORS (weekly % change):
{chr(10).join(f"  - {s['name']}: {s['change_pct']:+.2f}%" for s in sectors) if sectors else "  (sector data unavailable this week)"}

VIETNAM MACRO:
- USD/VND: {macro.get('usd_vnd')} ({_fmt(macro.get('usd_vnd_weekly_change_pct'), '%')} wow)
- Interbank overnight: {_fmt(macro.get('interbank_rate'), '%')}
- SBV OMO net: {_fmt(macro.get('sbv_omo_net_bn_vnd'))} Bn VND (available: {macro.get('sbv_omo_available')})

GLOBAL CROSS-ASSET:
- DXY: {global_m.get('dxy_close')} ({_fmt(global_m.get('dxy_weekly_change_pct'), '%')})
- Gold: {global_m.get('gold_close')} USD/oz ({_fmt(global_m.get('gold_weekly_change_pct'), '%')})
- WTI: {global_m.get('wti_close')} USD/bbl ({_fmt(global_m.get('wti_weekly_change_pct'), '%')})

CRYPTO:
- BTC: {crypto.get('btc_close')} USD ({_fmt(crypto.get('btc_weekly_change_pct'), '%')})
- ETH: {crypto.get('eth_close')} USD ({_fmt(crypto.get('eth_weekly_change_pct'), '%')})

FOREIGN NET FLOW (WEEKLY): {_fmt(week_data.get('foreign_net_weekly_bn_vnd'))} Bn VND (positive = net buying)

SESSION TONE HINT: {tone_hint}

Write a markdown file with EXACTLY this structure. Output ONLY the markdown —
no preamble, no code fences, no explanation.

The frontmatter must be valid YAML. Numeric fields are raw numbers (no quotes,
no commas, no units). Nullable fields must be `null` (not the string "null")
when data is unavailable. Date and string fields are quoted.

---
title: "Weekly Market View: {title_date} — {{{{descriptive headline}}}}"
date: "{friday}"
week_start: "{monday}"
week_end: "{friday}"
vn_index_open: {vn.get('open')}
vn_index_high: {vn.get('high')}
vn_index_low: {vn.get('low')}
vn_index_close: {vn.get('close')}
vn_index_weekly_change_pct: {vn.get('weekly_change_pct')}
avg_daily_liquidity_bn_vnd: {vn.get('avg_daily_liquidity_bn_vnd')}
foreign_net_weekly_bn_vnd: {week_data.get('foreign_net_weekly_bn_vnd')}
dxy_close: {global_m.get('dxy_close') if global_m.get('dxy_close') is not None else 'null'}
dxy_weekly_change_pct: {global_m.get('dxy_weekly_change_pct') if global_m.get('dxy_weekly_change_pct') is not None else 'null'}
usd_vnd: {macro.get('usd_vnd') if macro.get('usd_vnd') is not None else 'null'}
usd_vnd_weekly_change_pct: {macro.get('usd_vnd_weekly_change_pct') if macro.get('usd_vnd_weekly_change_pct') is not None else 'null'}
btc_close: {crypto.get('btc_close') if crypto.get('btc_close') is not None else 'null'}
btc_weekly_change_pct: {crypto.get('btc_weekly_change_pct') if crypto.get('btc_weekly_change_pct') is not None else 'null'}
gold_close: {global_m.get('gold_close') if global_m.get('gold_close') is not None else 'null'}
gold_weekly_change_pct: {global_m.get('gold_weekly_change_pct') if global_m.get('gold_weekly_change_pct') is not None else 'null'}
wti_close: {global_m.get('wti_close') if global_m.get('wti_close') is not None else 'null'}
wti_weekly_change_pct: {global_m.get('wti_weekly_change_pct') if global_m.get('wti_weekly_change_pct') is not None else 'null'}
session_tone: "{tone_hint}"
chart_vnindex: "/charts/vnindex_weekly_{friday}.png"
chart_sectors: "/charts/sector_performance_{friday}.png"
---

## Executive Summary
~100 words. Top-down synthesis. 3-5 bullet points of the most important takeaways.

## Vietnam Macro Pulse
- USD/VND movement and SBV actions (policy, T-bill issuance, OMO)
- Interbank liquidity conditions
- Key macro releases this week (CPI, PMI, trade balance, GDP if any)
- Forward-looking signals for Vietnam

## VN-Index: Weekly Review
- Open, close, high, low for the week
- Chart: ![VN-Index Weekly](chart_vnindex)
- Candlestick pattern analysis
- Volume analysis (compare to recent average)
- Market breadth (advancers vs decliners — estimate if exact data unavailable)
- Foreign flow narrative — magnitude, which stocks, strategic implications
- Reference previous week's close for trend continuity

## Sector Spotlight: {{{{rotating sector}}}}
- Pick the most notable/volatile sector this week. Do NOT default to banking each week.
  Rotate: Steel (HPG, HSG), Real Estate (VHM, VIC, NVL, VRE), Consumer (VNM, MSN, MWG),
  Technology (FPT), Securities (SSI, VND, HCM), Industrial (REE, GEX), Oil & Gas (PLX, GAS).
- Top movers with ticker-level detail
- Catalyst analysis (policy, earnings, rotation, foreign positioning)
- Forward outlook
- Chart: ![Sector Performance](chart_sectors)

## Global Cross-Asset Snapshot
1-2 sentences each:
- DXY: strength/weakness, EM and VND implication
- Crypto: BTC/ETH direction, any major catalysts
- Commodities: Gold drivers, Oil supply/demand (OPEC+, geopolitics)
- Implications for Vietnam: 1-2 sentences tying global to VN market

## The Week Ahead
- Key events (Vietnam data releases, holidays, regional events)
- 2-3 scenarios for VN-Index next week (bull/base/bear with rough level ranges)
- Key support/resistance levels to watch

*Academic exercise — not investment advice. Prepared by Nguyen Vu Truong Huy.*

QUALITY RULES:
- Bloomberg/FT tone. Quantify with specific numbers — never "significant increase" without numbers.
- Reference specific tickers (VCB, BID, CTG, HPG, HSG, VHM, VIC, VNM, MSN, FPT, MWG, etc.).
- If data is unavailable, say so explicitly ("data unavailable this week").
- Maintain week-over-week continuity (reference the prior week's narrative arc).
- Sector Spotlight must show genuine industry expertise — regulatory environment,
  business dynamics, competitive landscape, not surface-level description.
- Global section must tie back to Vietnam implications.
- All numbers in frontmatter are raw values; date/title are quoted strings.
- The session_tone MUST be: "positive" if weekly_change_pct > 0.5, "negative" if < -0.5, "neutral" otherwise.
- The last line of the body must be the academic exercise disclaimer.
"""


def call_llm(prompt: str) -> str:
    """Call MiniMax M3 via Ollama Cloud /chat endpoint. Returns raw text."""
    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY or LLM_API_KEY environment variable not set")
        sys.exit(1)
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
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: LLM API returned HTTP {e.code}: {body[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: LLM API call failed: {e}")
        sys.exit(1)

    text = result.get("message", {}).get("content", "").strip()
    if text.startswith("```markdown"):
        text = text[len("```markdown"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ---------------------------------------------------------------------------
# Validation + file write
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_FIELDS = [
    "title", "date", "week_start", "week_end",
    "vn_index_open", "vn_index_high", "vn_index_low", "vn_index_close",
    "vn_index_weekly_change_pct",
    "avg_daily_liquidity_bn_vnd", "foreign_net_weekly_bn_vnd",
    "session_tone",
]

NULLABLE_FRONTMATTER_FIELDS = [
    "dxy_close", "dxy_weekly_change_pct",
    "usd_vnd", "usd_vnd_weekly_change_pct",
    "btc_close", "btc_weekly_change_pct",
    "gold_close", "gold_weekly_change_pct",
    "wti_close", "wti_weekly_change_pct",
]


def validate_frontmatter(content: str, friday: str) -> bool:
    """Check that generated content has a valid YAML frontmatter block with
    all required fields and a valid session_tone enum value.
    """
    if not content.startswith("---"):
        print("ERROR: Content does not start with --- frontmatter delimiter")
        return False
    end = content.find("\n---", 3)
    if end == -1:
        print("ERROR: Could not find closing --- frontmatter delimiter")
        return False
    fm = content[3:end].strip()

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if not re.search(rf"^{re.escape(field)}\s*:", fm, flags=re.MULTILINE):
            print(f"ERROR: Missing required frontmatter field: {field}")
            return False

    for field in NULLABLE_FRONTMATTER_FIELDS:
        if not re.search(rf"^{re.escape(field)}\s*:", fm, flags=re.MULTILINE):
            print(f"ERROR: Missing nullable frontmatter field: {field}")
            return False

    # session_tone must be one of the enum values
    m = re.search(r"^session_tone\s*:\s*\"?(\w+)\"?", fm, flags=re.MULTILINE)
    if not m:
        print("ERROR: session_tone not parseable")
        return False
    tone = m.group(1)
    if tone not in ("positive", "negative", "neutral"):
        print(f"ERROR: session_tone must be one of positive/negative/neutral, got: {tone}")
        return False

    # friday date check
    m = re.search(r"^date\s*:\s*\"?(\d{4}-\d{2}-\d{2})\"?", fm, flags=re.MULTILINE)
    if not m or m.group(1) != friday:
        print(f"ERROR: date field must be {friday}, got {m.group(1) if m else 'missing'}")
        return False

    return True


def write_file(content: str, friday: str) -> Path:
    """Write the markdown file to the content directory."""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CONTENT_DIR / f"{friday}.md"
    if filepath.exists():
        print(f"  [info] File {filepath} already exists, overwriting")
    filepath.write_text(content, encoding="utf-8")
    print(f"  [ok] Written: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Weekly Market View markdown post."
    )
    parser.add_argument(
        "--week", help="Friday date in YYYY-MM-DD (default: most recent completed Friday ICT)",
        default=None,
    )
    parser.add_argument(
        "--charts-only", action="store_true",
        help="Regenerate charts only and skip the LLM call.",
    )
    parser.add_argument(
        "--skip-charts", action="store_true",
        help="Skip chart generation (LLM call only).",
    )
    args = parser.parse_args()

    monday, friday = get_week_dates(args.week)
    print(f"Week: {monday} (Mon) – {friday} (Fri) ICT")

    # 1. Fetch data
    print("[1/4] Fetching data…")
    week_data = {
        "vnindex": fetch_vnindex_weekly(monday, friday),
        "macro": {
            "usd_vnd": None, "usd_vnd_weekly_change_pct": None,
            "interbank_rate": fetch_interbank_rate(),
        },
        "global": fetch_global_markets(monday, friday),
        "crypto": fetch_crypto_weekly(monday, friday),
        "sectors": fetch_sector_performance(monday, friday),
        "foreign_net_weekly_bn_vnd": fetch_foreign_flow_weekly(monday, friday),
    }
    # USD/VND separately (vnstock Macro first, yfinance fallback)
    usd, usd_pct = fetch_usd_vnd()
    week_data["macro"]["usd_vnd"] = usd
    week_data["macro"]["usd_vnd_weekly_change_pct"] = usd_pct
    # SBV OMO
    sbv = fetch_sbv_omo() or {"net_bn_vnd": None, "available": False}
    week_data["macro"]["sbv_omo_net_bn_vnd"] = sbv.get("net_bn_vnd")
    week_data["macro"]["sbv_omo_available"] = sbv.get("available", False)

    # Daily data for chart (always fetch, even if main OHLCV failed)
    week_data["_daily_df"] = fetch_vnindex_daily_for_chart(monday, friday)

    # 2. Generate charts
    charts: list[str] = []
    if not args.skip_charts:
        print("[2/4] Generating charts…")
        charts = generate_charts(week_data, friday)
    else:
        print("[2/4] Skipping charts (--skip-charts)")

    if args.charts_only:
        print(f"\nDone (charts-only). Wrote {len(charts)} chart(s).")
        return

    # 3. LLM call
    print("[3/4] Calling LLM (MiniMax M3 via Ollama Cloud)…")
    prompt = build_prompt(week_data, monday, friday)
    content = call_llm(prompt)

    # 4. Validate + write
    print("[4/4] Validating and writing…")
    if not validate_frontmatter(content, friday):
        print("ERROR: Generated content failed validation, exiting")
        sys.exit(1)
    filepath = write_file(content, friday)

    print(f"\nDone! Weekly Market View written to: {filepath}")
    print(f"Charts: {len(charts)}")
    print(f"Next: git add -A && git commit -m 'weekly: market view {friday}' && git push")


if __name__ == "__main__":
    main()
