import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db
from utils.common import today
from utils.scoring import readiness, skill_gaps
from utils.ui import CURRENT_USER as U, header


def gap_table(profile: dict, opps: list[dict], resources: pd.DataFrame):
    gaps = skill_gaps(profile, opps)
    rows = []
    for skill, n in gaps:
        r = resources[resources["skill"] == skill]
        rows.append({"skill": skill, "needed_by": n,
                     "free_resources": "; ".join(f"{x.title} ({x.url})" for x in r.itertuples()) or "None yet - add one in Resources"})
    return gaps, rows


def render():
    header("Career Readiness Radar", "Scores come from your skill list: each category score is the share of its listed skills you have.")
    profile = db.get_profile(U)
    scores = readiness(profile["skills"])
    cats = list(scores)
    fig = go.Figure(go.Scatterpolar(r=[*scores.values(), scores[cats[0]]], theta=[*cats, cats[0]], fill="toself",
                                    line_color="#0F766E"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False, height=420,
                      margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.metric("Overall readiness", f"{sum(scores.values()) / len(scores):.0f}%")

    st.subheader("Skill gaps across your active opportunities")
    opps = db.list_opportunities(U).to_dict("records")
    gaps, rows = gap_table(profile, opps, db.list_resources(U))
    if not rows:
        st.success("No gaps found for tracked opportunities, or none tracked yet.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    if st.button("Create study tasks for the top 3 gaps", type="primary"):
        existing = set(db.list_tasks(U)["title"])
        added = 0
        for skill, _ in gaps[:3]:
            title = f"Learn: {skill}"
            if title not in existing:
                db.insert("study_tasks", U, {"title": title, "skill": skill, "minutes": 60,
                                             "due_date": None, "is_demo": 0})
                added += 1
        st.success(f"Added {added} task(s). Find them in the Daily Study Planner.")
