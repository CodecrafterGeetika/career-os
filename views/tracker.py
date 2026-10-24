import pandas as pd
import streamlit as st

import database as db
from utils.common import clean_str, days_left, today
from utils.scoring import eligibility
from utils.ui import CURRENT_USER as U, header
from utils.validation import validate_opportunity
from views._forms import opportunity_form


def scored_frame(profile: dict, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(match=[], match_label=[], days_left=[])
    res = [eligibility(profile, r) for r in df.to_dict("records")]
    out = df.copy()
    out["match"] = [r["score"] for r in res]
    out["match_label"] = [r["label"] for r in res]
    out["days_left"] = [days_left(d) for d in out["deadline"]]
    return out


def render():
    header("Job and Internship Tracker", "Save opportunities, see how well you match, and move them through your pipeline.")
    profile = db.get_profile(U)
    df = scored_frame(profile, db.list_opportunities(U))
    df = df[df["kind"].isin(["Job", "Internship"])] if not df.empty else df

    with st.expander("Add an opportunity"):
        ok, data, status = opportunity_form(["Job", "Internship"], "add_opp")
        if ok:
            errs = validate_opportunity(data)
            if errs:
                st.error(" ".join(errs))
            else:
                oid = db.insert("opportunities", U, {**data, "is_demo": 0})
                db.set_status(U, oid, status)
                st.success("Saved.")
                st.rerun()

    c1, c2, c3 = st.columns([2, 2, 2])
    kinds = c1.multiselect("Type", ["Job", "Internship"], default=["Job", "Internship"])
    statuses = c2.multiselect("Status", db.STATUSES, default=db.STATUSES)
    q = c3.text_input("Search title or organisation")
    min_match = st.slider("Minimum match %", 0, 100, 0, 5)
    if df.empty:
        st.info("No opportunities yet. Add one above.")
        return
    f = df[df["kind"].isin(kinds) & df["status"].isin(statuses) & (df["match"] >= min_match)]
    if q:
        mask = f["title"].str.contains(q, case=False, na=False) | f["org"].str.contains(q, case=False, na=False)
        f = f[mask]
    show = f[["id", "title", "org", "kind", "status", "deadline", "days_left", "match", "match_label"]]
    st.dataframe(show, hide_index=True, use_container_width=True,
                 column_config={"match": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d"),
                                "days_left": "Days left"})

    st.subheader("Edit or update")
    if f.empty:
        st.caption("No rows match the filters.")
        return
    labels = {int(r.id): f"#{r.id} {r.title}" for r in f.itertuples()}
    oid = st.selectbox("Choose an opportunity", list(labels), format_func=labels.get)
    row = f[f["id"] == oid].iloc[0].to_dict()
    result = eligibility(profile, row)
    st.caption(" | ".join(result["reasons"]))
    ok, data, status = opportunity_form(["Job", "Internship"], f"edit_{oid}", row)
    if ok:
        errs = validate_opportunity(data)
        if errs:
            st.error(" ".join(errs))
        else:
            db.update("opportunities", U, oid, data)
            db.set_status(U, oid, status, today().isoformat() if status == "Applied" else None)
            st.success("Updated.")
            st.rerun()
    if clean_str(row.get("url")):
        st.link_button("Open official page", row["url"])
    if st.button("Delete this opportunity", key=f"del_{oid}"):
        db.delete("opportunities", U, oid)
        st.rerun()
