"""Plan rules: open tasks are sorted by due date (earliest first, undated last), then shorter first.
Minutes are packed into days of `daily_hours`; a task may be split across days. A chunk is flagged
`late` if it lands after the task's due date."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from utils.common import clean_num, parse_date


def build_plan(tasks: list[dict], daily_hours: float, start: date, days: int = 7) -> list[dict]:
    budget = int(daily_hours * 60)
    if budget <= 0:
        return []
    open_tasks = [t for t in tasks if not t.get("done") and clean_num(t.get("minutes")) > 0]
    open_tasks.sort(key=lambda t: (parse_date(t.get("due_date")) or date.max, clean_num(t["minutes"])))
    plan, idx, remaining = [], 0, budget
    for t in open_tasks:
        mins, due = int(clean_num(t["minutes"])), parse_date(t.get("due_date"))
        while mins > 0 and idx < days:
            chunk = min(mins, remaining)
            day = start + timedelta(days=idx)
            plan.append({"date": day, "task_id": int(t["id"]), "title": t["title"], "minutes": chunk,
                         "late": bool(due and day > due)})
            mins -= chunk
            remaining -= chunk
            if remaining == 0:
                idx, remaining = idx + 1, budget
    return plan


def weekly_progress(tasks: pd.DataFrame, ref: date) -> pd.DataFrame:
    """Completed tasks and minutes for each of the 7 days ending on `ref`."""
    rows = [{"date": ref - timedelta(days=i), "tasks": 0, "minutes": 0} for i in range(6, -1, -1)]
    lookup = {r["date"]: r for r in rows}
    if not tasks.empty:
        for _, t in tasks[tasks["done"] == 1].iterrows():
            d = parse_date(t["completed_on"])
            if d in lookup:
                lookup[d]["tasks"] += 1
                lookup[d]["minutes"] += int(t["minutes"])
    return pd.DataFrame(rows)
