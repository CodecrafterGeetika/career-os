
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
    st.markdown(
    """
    <div style="padding: 1.5rem 0 1rem 0;">
        <h1 style="margin-bottom: 0.4rem;">CareerOS CSE</h1>
        <p style="font-size: 1rem; color: #64748b; margin-top: 0;">
            Your career command centre — opportunities, deadlines & preparation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

    p = db.get_profile(U)
    opps = scored_frame(p, db.list_opportunities(U))
    tasks = db.list_tasks(U)

    if not opps.empty and "is_demo" in opps.columns:
        if opps["is_demo"].fillna(0).eq(1).any():
            demo_banner()

    # Active opportunities exclude rejected applications.
    active = (
        opps[~opps["status"].isin(["Rejected"])].copy()
        if not opps.empty
        else opps.copy()
    )

    # Only opportunities with known, non-past deadlines are included.
    if not active.empty and "days_left" in active.columns:
        upcoming = active[
            active["days_left"].notna() & (active["days_left"] >= 0)
        ].copy()
    else:
        upcoming = active.iloc[0:0].copy()

    wk = weekly_progress(tasks, today())

    skill_scores = readiness(p.get("skills", {}))
    ready = sum(skill_scores.values()) / len(skill_scores) if skill_scores else 0

    # Key metrics
    st.subheader("Your progress")

    c = st.columns(4)

    with c[0]:
        metric_card("Active opportunities", len(active), "Excluding rejected")

    with c[1]:
        nxt = (
            upcoming.sort_values("days_left").iloc[0]
            if not upcoming.empty
            else None
        )

        if nxt is None:
            metric_card("Next deadline", "—", "No upcoming deadlines")
        else:
            days = int(nxt["days_left"])
            label = "Due today" if days == 0 else f"{days} days left"
            metric_card("Next deadline", label, str(nxt["title"]))

    with c[2]:
        metric_card("Readiness", f"{ready:.0f}%", "Based on your skills")

    with c[3]:
        completed = int(wk["tasks"].sum()) if not wk.empty else 0
        minutes = int(wk["minutes"].sum()) if not wk.empty else 0
        metric_card("Tasks this week", completed, f"{minutes} study minutes")

    st.divider()

    # Pipeline and match scores
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Application pipeline")
        st.caption("See where your opportunities currently stand.")

        if opps.empty:
            st.info(
                "Your tracker is empty. Add a verified job, internship, "
                "or exam opportunity to start building your pipeline."
            )
        else:
            counts = (
                opps["status"]
                .value_counts()
                .reindex(db.STATUSES, fill_value=0)
                .rename_axis("Status")
                .reset_index(name="Opportunities")
            )

            fig = px.bar(
                counts,
                x="Status",
                y="Opportunities",
                text="Opportunities",
            )
            fig.update_traces(
                marker_color="#0F766E",
                textposition="outside",
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                margin=dict(l=8, r=8, t=20, b=8),
                showlegend=False,
                xaxis_title=None,
                yaxis_title="Number of opportunities",
                yaxis=dict(rangemode="tozero", dtick=1),
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Best skill matches")
        st.caption("Prioritize opportunities that fit your current skills.")

        if active.empty:
            st.info(
                "Your best matches will appear here after you add opportunities."
            )
        elif "match" not in active.columns:
            st.info("Match scores are not available for the current records.")
        else:
            columns = [
                col
                for col in ["title", "kind", "match", "match_label"]
                if col in active.columns
            ]

            top = active.sort_values("match", ascending=False).head(5)

            display = top[columns].copy()
            rename = {
                "title": "Opportunity",
                "kind": "Type",
                "match": "Match score",
                "match_label": "Match level",
            }
            display = display.rename(columns=rename)

            config = {}
            if "Match score" in display.columns:
                config["Match score"] = st.column_config.ProgressColumn(
                    "Match score",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                )

            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
                column_config=config,
            )

    st.divider()

    # Upcoming deadlines
    st.subheader("Upcoming deadlines")
    st.caption("Keep track of applications and exams that are approaching.")

    if upcoming.empty:
        st.success("You're all caught up — no upcoming deadlines recorded.")
        st.caption(
            "Add a deadline to an opportunity in your tracker to see it here."
        )
    else:
        deadline_rows = upcoming.sort_values("days_left").head(8).copy()

        def urgency(days):
            days = int(days)
            if days == 0:
                return "Due today"
            if days <= 3:
                return "Urgent"
            if days <= 7:
                return "This week"
            return "Upcoming"

        deadline_rows["Priority"] = deadline_rows["days_left"].apply(urgency)

        columns = [
            col
            for col in ["title", "kind", "deadline", "days_left", "Priority"]
            if col in deadline_rows.columns
        ]

        deadline_display = deadline_rows[columns].rename(
            columns={
                "title": "Opportunity",
                "kind": "Type",
                "deadline": "Deadline",
                "days_left": "Days left",
            }
        )

        st.dataframe(
            deadline_display,
            hide_index=True,
            use_container_width=True,
        )

    st.caption(
        "Tip: Update your skills and application statuses regularly to keep "
        "your matches and dashboard useful."
    )
