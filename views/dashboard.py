import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from utils.common import today
from utils.planner import weekly_progress
from utils.scoring import readiness
from utils.ui import CURRENT_USER as U, demo_banner, header, metric_card
from views.tracker import scored_frame


def render():
    header("Dashboard", "Your pipeline, deadlines, and preparation at a glance.")
    p = db.get_profile(U)
    opps = scored_frame(p, db.list_opportunities(U))
    tasks = db.list_tasks(U)
    if not opps.empty and opps["is_demo"].eq(1).any():
        demo_banner()
    active = opps[~opps["status"].isin(["Rejected"])] if not opps.empty else opps
    upcoming = active[active["days_left"].notna() & (active["days_left"] >= 0)] if not active.empty else active
    wk = weekly_progress(tasks, today())
    ready = sum(readiness(p["skills"]).values()) / 6

    c = st.columns(4)
    with c[0]:
        metric_card("Active opportunities", len(active))
    with c[1]:
        nxt = upcoming.sort_values("days_left").iloc[0] if not upcoming.empty else None
        metric_card("Next deadline", f"{int(nxt['days_left'])} days" if nxt is not None else "None", nxt["title"] if nxt is not None else "")
    with c[2]:
        metric_card("Readiness", f"{ready:.0f}%", "from your skill list")
    with c[3]:
        metric_card("Done this week", int(wk["tasks"].sum()), f"{int(wk['minutes'].sum())} minutes")

    left, right = st.columns(2)
    with left:
        st.subheader("Pipeline")
        if opps.empty:
            st.info("Add opportunities in the tracker.")
        else:
            counts = opps["status"].value_counts().reindex(db.STATUSES, fill_value=0).reset_index()
            counts.columns = ["status", "count"]
            fig = px.bar(counts, x="status", y="count")
            fig.update_traces(marker_color="#0F766E")
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Best matches")
        if active.empty:
            st.caption("Nothing to rank yet.")
        else:
            top = active.sort_values("match", ascending=False).head(5)
            st.dataframe(top[["title", "kind", "match", "match_label"]], hide_index=True, use_container_width=True,
                         column_config={"match": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d")})
    st.subheader("Upcoming deadlines")
    if upcoming.empty:
        st.caption("No upcoming deadlines.")
    else:
        st.dataframe(upcoming.sort_values("days_left").head(6)[["title", "kind", "deadline", "days_left"]],
                     hide_index=True, use_container_width=True)
