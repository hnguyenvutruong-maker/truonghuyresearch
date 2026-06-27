#!/usr/bin/env python3
"""Shared narrative memory for weekly, monthly, and quarterly market views."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
MEMORY_FILE = PROJECT_ROOT / "src" / "content" / "market-views" / "_market_memory.json"
MONTHLY_SUMMARY_FILE = PROJECT_ROOT / "src" / "content" / "monthly-views" / "_monthly_summary.json"


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else default
    except Exception:
        return default


def _extract_title(markdown: str) -> str:
    match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', markdown, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section(markdown: str, heading: str, max_chars: int = 900) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    text = re.sub(r"\s+", " ", match.group(1)).strip()
    return text[:max_chars]


def load_market_memory() -> dict[str, Any]:
    default = {
        "last_updated": "",
        "weekly": {},
        "monthly": {},
        "quarterly": {},
        "continuity_rules": [
            "Weekly notes should update, not reset, the active monthly and quarterly narrative.",
            "Monthly notes should reconcile the weekly tape and preserve the quarter-level thesis.",
            "Quarterly memory is the long-term anchor for levels, risks, and sector rotation.",
            "Contradictions between weekly, monthly, and quarterly views must be explicitly resolved.",
        ],
    }
    return _load_json(MEMORY_FILE, default)


def save_market_memory(memory: dict[str, Any]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


def _monthly_snapshot() -> dict[str, Any]:
    summary = _load_json(
        MONTHLY_SUMMARY_FILE,
        {"last_updated": "", "months_covered": [], "current_month": {}, "prior_months": []},
    )
    current = summary.get("current_month", {})
    return {
        "last_updated": summary.get("last_updated", ""),
        "months_covered": summary.get("months_covered", []),
        "vn_index_trend": current.get("vn_index_trend", ""),
        "key_themes": current.get("key_themes", []),
        "macro_regime": current.get("macro_regime", ""),
        "foreign_flow_direction": current.get("foreign_flow_direction", ""),
        "forward_risks": current.get("forward_risks", []),
    }


def _quarterly_snapshot(quarterly_summary: dict[str, Any]) -> dict[str, Any]:
    summary = quarterly_summary.get("summary", {}) if quarterly_summary else {}
    return {
        "quarter": quarterly_summary.get("quarter", ""),
        "last_updated": quarterly_summary.get("last_updated", ""),
        "weeks_covered": quarterly_summary.get("weeks_covered", []),
        "vn_index_trend": summary.get("vn_index_trend", ""),
        "key_themes": summary.get("key_themes", []),
        "macro_environment": summary.get("macro_environment", ""),
        "technical_levels": summary.get("technical_levels", {}),
        "forward_risks": summary.get("forward_risks", []),
    }


def format_market_memory_for_llm(memory: dict[str, Any]) -> str:
    if not memory:
        return "(No shared market memory available yet.)"

    monthly = memory.get("monthly", {})
    quarterly = memory.get("quarterly", {})
    weekly = memory.get("weekly", {})
    rules = memory.get("continuity_rules", [])

    def join(values: Any, limit: int = 6) -> str:
        if not values:
            return "N/A"
        if isinstance(values, list):
            return "; ".join(str(v) for v in values[:limit])
        return str(values)

    lines = [
        "SHARED MARKET MEMORY",
        f"Last Updated: {memory.get('last_updated', 'N/A')}",
        "",
        "Latest Weekly:",
        f"- Week End: {weekly.get('week_end', 'N/A')}",
        f"- Title: {weekly.get('title', 'N/A')}",
        f"- Executive Summary: {weekly.get('executive_summary', 'N/A')}",
        "",
        "Current Monthly State:",
        f"- Last Month: {monthly.get('last_updated', 'N/A')}",
        f"- VN-Index Trend: {monthly.get('vn_index_trend', 'N/A')}",
        f"- Key Themes: {join(monthly.get('key_themes'))}",
        f"- Macro Regime: {monthly.get('macro_regime', 'N/A')}",
        f"- Foreign Flow: {monthly.get('foreign_flow_direction', 'N/A')}",
        f"- Forward Risks: {join(monthly.get('forward_risks'), 4)}",
        "",
        "Current Quarterly State:",
        f"- Quarter: {quarterly.get('quarter', 'N/A')}",
        f"- Weeks Covered: {join(quarterly.get('weeks_covered'))}",
        f"- VN-Index Trend: {quarterly.get('vn_index_trend', 'N/A')}",
        f"- Key Themes: {join(quarterly.get('key_themes'))}",
        f"- Macro Environment: {quarterly.get('macro_environment', 'N/A')}",
        f"- Technical Levels: {json.dumps(quarterly.get('technical_levels', {}), ensure_ascii=False)}",
        f"- Forward Risks: {join(quarterly.get('forward_risks'), 5)}",
        "",
        "Continuity Rules:",
        *[f"- {rule}" for rule in rules],
    ]
    return "\n".join(lines)


def save_weekly_market_memory(
    week_end: date,
    commentary: str,
    quarterly_summary: dict[str, Any],
) -> dict[str, Any]:
    memory = load_market_memory()
    memory["last_updated"] = week_end.isoformat()
    memory["weekly"] = {
        "week_end": week_end.isoformat(),
        "title": _extract_title(commentary),
        "executive_summary": _extract_section(commentary, "Executive Summary"),
    }
    memory["monthly"] = _monthly_snapshot()
    memory["quarterly"] = _quarterly_snapshot(quarterly_summary)
    save_market_memory(memory)
    return memory


def save_monthly_market_memory(
    month_label: str,
    commentary: str,
    monthly_summary: dict[str, Any],
) -> dict[str, Any]:
    memory = load_market_memory()
    current = monthly_summary.get("current_month", {}) if monthly_summary else {}
    memory["last_updated"] = month_label
    memory["monthly"] = {
        "last_updated": month_label,
        "months_covered": monthly_summary.get("months_covered", []),
        "title": _extract_title(commentary),
        "executive_summary": _extract_section(commentary, "Executive Summary"),
        "vn_index_trend": current.get("vn_index_trend", ""),
        "key_themes": current.get("key_themes", []),
        "macro_regime": current.get("macro_regime", ""),
        "foreign_flow_direction": current.get("foreign_flow_direction", ""),
        "forward_risks": current.get("forward_risks", []),
    }
    save_market_memory(memory)
    return memory
