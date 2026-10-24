from __future__ import annotations

from datetime import date, datetime

import pandas as pd


def today() -> date:
    return date.today()


def parse_date(v) -> date | None:
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def clean_str(v) -> str:
    return "" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)


def clean_num(v, default: float = 0.0) -> float:
    try:
        return default if v is None or pd.isna(v) else float(v)
    except (TypeError, ValueError):
        return default


def parse_list(s) -> list[str]:
    """'Python, SQL ,python' -> ['python', 'sql'] (lowercased, de-duplicated, order kept)."""
    out: list[str] = []
    for part in clean_str(s).split(","):
        p = part.strip().lower()
        if p and p not in out:
            out.append(p)
    return out


def days_left(deadline, ref: date | None = None) -> int | None:
    d = parse_date(deadline)
    return None if d is None else (d - (ref or today())).days
