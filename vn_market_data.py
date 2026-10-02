"""
vn_market_data.py — VN-Index daily history shared by weekly_bot and monthly_bot.

vnstock used to be the primary source. Its PyPI project was quarantined in
Sep 2026, so it is no longer installed; these sources need only `requests`
and (optionally) `yfinance`:

  1. VNDirect dchart API (TradingView-style daily bars for VNINDEX)
  2. yfinance ^VNINDEX.VN

Callers must treat an empty result as "no data" and stop. Never substitute
synthetic index values: they would be published as if they were real.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Optional

try:
    import requests as requests_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

ICT = timezone(timedelta(hours=7))

# VN-Index has traded between roughly 900 and 2,000 for years; anything far
# outside this band means the source returned the wrong instrument or units.
_INDEX_MIN, _INDEX_MAX = 300.0, 5000.0

Row = dict[str, Any]
Logger = Callable[[str, str], None]


def _valid(row: Row) -> bool:
    try:
        o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
    except (KeyError, TypeError, ValueError):
        return False
    if not all(_INDEX_MIN <= v <= _INDEX_MAX for v in (o, h, l, c)):
        return False
    return l <= min(o, c) + 1e-6 and h >= max(o, c) - 1e-6


def _clean(rows: list[Row], start: date, end: date) -> list[Row]:
    by_day: dict[str, Row] = {}
    for r in rows:
        if start.isoformat() <= r["time"] <= end.isoformat() and _valid(r):
            by_day[r["time"]] = r
    return [by_day[k] for k in sorted(by_day)]


def _from_vndirect(start: date, end: date) -> list[Row]:
    if not HAS_REQUESTS:
        return []
    t0 = int(datetime(start.year, start.month, start.day, tzinfo=ICT).timestamp())
    t1 = int(datetime(end.year, end.month, end.day, 23, 59, tzinfo=ICT).timestamp())
    resp = requests_lib.get(
        "https://dchart-api.vndirect.com.vn/dchart/history",
        params={"resolution": "D", "symbol": "VNINDEX", "from": t0, "to": t1},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("s") != "ok":
        return []
    rows: list[Row] = []
    for t, o, h, l, c, v in zip(data["t"], data["o"], data["h"], data["l"], data["c"], data["v"]):
        day = datetime.fromtimestamp(int(t), tz=ICT).date().isoformat()
        rows.append({"time": day, "open": float(o), "high": float(h),
                     "low": float(l), "close": float(c), "volume": float(v)})
    return rows


def _from_yfinance(start: date, end: date) -> list[Row]:
    if not HAS_YFINANCE:
        return []
    df = yf.Ticker("^VNINDEX.VN").history(start=start, end=end + timedelta(days=1))
    if df is None or df.empty:
        return []
    rows: list[Row] = []
    for ts, r in df.iterrows():
        rows.append({"time": ts.date().isoformat(), "open": float(r["Open"]),
                     "high": float(r["High"]), "low": float(r["Low"]),
                     "close": float(r["Close"]), "volume": float(r["Volume"])})
    return rows


def fetch_vnindex_daily(start: date, end: date, log: Logger) -> tuple[list[Row], Optional[str]]:
    """Return (daily rows within [start, end] sorted by date, source name).

    Each row is {time: "YYYY-MM-DD", open, high, low, close, volume}.
    Returns ([], None) when no source produced usable data.
    """
    for name, fetch in (("vndirect", _from_vndirect), ("yfinance", _from_yfinance)):
        try:
            rows = _clean(fetch(start, end), start, end)
        except Exception as e:  # network, JSON shape, rate limit
            log("VNI", f"  {name} failed: {e}")
            continue
        if rows:
            log("VNI", f"  {name}: {len(rows)} sessions {rows[0]['time']} → {rows[-1]['time']}")
            return rows, name
        log("VNI", f"  {name}: no usable rows for {start} → {end}")
    return [], None


def summarize(rows: list[Row]) -> dict[str, Any]:
    """OHLC summary of a run of daily rows (open of first, close of last)."""
    o = rows[0]["open"]
    c = rows[-1]["close"]
    return {
        "open": round(o, 2),
        "high": round(max(r["high"] for r in rows), 2),
        "low": round(min(r["low"] for r in rows), 2),
        "close": round(c, 2),
        "change_pct": round((c - o) / o * 100, 2),
        "trading_days": len(rows),
    }


def avg_daily_liquidity_bn(rows: list[Row], avg_share_price_vnd: Optional[float]) -> Optional[float]:
    """Average daily HOSE turnover in bn VND, from share volume × average share price.

    Returns None when the inputs are missing or the result is implausible
    (HOSE turnover has been roughly VND 5,000–60,000bn a day).
    """
    if not avg_share_price_vnd or not rows:
        return None
    vols = [r.get("volume") or 0 for r in rows]
    value = sum(vols) / len(vols) * avg_share_price_vnd / 1e9
    if not 1_000 <= value <= 100_000:
        return None
    return round(value, 2)


def close_and_change(series: Any, start: date, end: date) -> tuple[Optional[float], Optional[float]]:
    """Close on the last session <= end and % change vs the last close before start.

    `series` is a pandas Series of closes indexed by timestamp that also covers
    some sessions before `start`. Returns (close, change_pct); the change is
    None when no close before `start` is available.
    """
    series = series.dropna()
    days = [ts.date() for ts in series.index]
    in_period = [float(v) for d, v in zip(days, series.values) if start <= d <= end]
    prior = [float(v) for d, v in zip(days, series.values) if d < start]
    if not in_period:
        return None, None
    close = round(in_period[-1], 2)
    prev = prior[-1] if prior else None
    chg = round((in_period[-1] - prev) / prev * 100, 2) if prev else None
    return close, chg


def yaml_scalar(val: Any) -> str:
    """Format a frontmatter value: raw numbers (no thousands separators), null, quoted strings."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return repr(round(val, 2))
    return json.dumps(str(val), ensure_ascii=False)


def enforce_frontmatter(markdown: str, values: dict[str, Any]) -> str:
    """Overwrite frontmatter fields with the measured values.

    The LLM is asked to copy these numbers into the frontmatter, but it can
    drop, reformat or "correct" them. The data is the ground truth, so each
    key in `values` is replaced (or appended) after generation.
    """
    m = re.match(r"\A\s*---\s*\n(.*?)\n---", markdown, re.DOTALL)
    if not m:
        return markdown
    fm = m.group(1)
    for key, val in values.items():
        line = f"{key}: {yaml_scalar(val)}"
        pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
        if pattern.search(fm):
            fm = pattern.sub(lambda _: line, fm, count=1)
        else:
            fm = f"{fm}\n{line}"
    return f"---\n{fm}\n---" + markdown[m.end():]
