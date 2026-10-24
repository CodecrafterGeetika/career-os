from __future__ import annotations

import streamlit as st

from database import STATUSES
from utils.common import clean_num, clean_str, parse_date, parse_list, today


def opportunity_form(kinds: list[str], key: str, existing: dict | None = None):
    """Returns (submitted, data, status). `existing` pre-fills the form for editing."""
    e = existing or {}
    with st.form(key, clear_on_submit=existing is None):
        title = st.text_input("Title *", clean_str(e.get("title")))
        c1, c2 = st.columns(2)
        org = c1.text_input("Organisation", clean_str(e.get("org")))
        kind = c2.selectbox("Type", kinds, index=kinds.index(e["kind"]) if e.get("kind") in kinds else 0)
        c3, c4 = st.columns(2)
        location = c3.text_input("Location", clean_str(e.get("location")))
        status = c4.selectbox("Status", STATUSES, index=STATUSES.index(e["status"]) if e.get("status") in STATUSES else 0)
        existing_dl = parse_date(e.get("deadline"))
        has_dl = st.checkbox("Has a deadline", value=existing_dl is not None)
        dl = st.date_input("Deadline (from the official notice)", value=existing_dl or today())
        c5, c6 = st.columns(2)
        min_cgpa = c5.number_input("Minimum CGPA (0 = none)", 0.0, 10.0, clean_num(e.get("min_cgpa")), 0.1)
        branches = c6.text_input("Eligible branches, comma-separated (blank = any)", clean_str(e.get("branches")))
        skills = st.text_input("Required skills, comma-separated", clean_str(e.get("required_skills")))
        url = st.text_input("Official URL (optional)", clean_str(e.get("url")))
        notes = st.text_area("Notes", clean_str(e.get("notes")))
        submitted = st.form_submit_button("Save opportunity", type="primary")
    data = {"title": title.strip(), "org": org.strip(), "kind": kind, "location": location.strip(),
            "deadline": dl.isoformat() if has_dl else None, "min_cgpa": float(min_cgpa),
            "branches": ", ".join(parse_list(branches)), "required_skills": ", ".join(parse_list(skills)),
            "url": url.strip(), "notes": notes.strip()}
    return submitted, data, status
