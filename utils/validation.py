from __future__ import annotations

import re
from datetime import date

from database import KINDS
from utils.common import parse_date


def valid_url(u: str) -> bool:
    return not u or bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", u.strip(), re.I))


def validate_opportunity(d: dict) -> list[str]:
    errs = []
    if not (d.get("title") or "").strip():
        errs.append("Title is required.")
    if d.get("kind") not in KINDS:
        errs.append("Choose a valid type.")
    if d.get("deadline") and parse_date(d["deadline"]) is None:
        errs.append("Deadline must be a valid date.")
    cg = d.get("min_cgpa")
    if cg is not None and not (0 <= cg <= 10):
        errs.append("Minimum CGPA must be between 0 and 10.")
    if not valid_url(d.get("url") or ""):
        errs.append("URL must start with http:// or https://.")
    return errs


def validate_profile(d: dict) -> list[str]:
    errs = []
    if not (d.get("name") or "").strip():
        errs.append("Name is required.")
    if not (0 <= d.get("cgpa", 0) <= 10):
        errs.append("CGPA must be between 0 and 10.")
    if not (0 <= d.get("daily_hours", 0) <= 16):
        errs.append("Daily study hours must be between 0 and 16.")
    if not (2000 <= d.get("grad_year", 2000) <= date.today().year + 10):
        errs.append("Graduation year looks out of range.")
    return errs


def validate_task(d: dict) -> list[str]:
    errs = []
    if not (d.get("title") or "").strip():
        errs.append("Task title is required.")
    if not (5 <= int(d.get("minutes", 0)) <= 600):
        errs.append("Minutes must be between 5 and 600.")
    return errs
