import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from utils.common import parse_date, today
from utils.planner import build_plan, weekly_progress
from utils.ui import CURRENT_USER as U, header, metric_card
from utils.validation import validate_task


def render():
    header("Daily Study Planner", "Open tasks are packed into your daily hours, earliest deadline first.")
    profile = db.get_profile(U)
    tasks = db.list_tasks(U)
    hours = st.slider("Study hours per day", 0.5, 12.0, float(profile["daily_hours"]), 0.5)
    plan = build_plan(tasks.to_dict("records"), hours, today())

    todays = [p for p in plan if p["date"] == today()]
    st.subheader("Today")
    if not todays:
        st.info("Nothing planned for today. Add a task below.")
    for p in todays:
        done = st.checkbox(f"{p['title']} - {p['minutes']} min" + ("  (past due date)" if p["late"] else ""),
                           key=f"chk_{p['task_id']}_{p['date']}")
        if done:
            db.set_task_done(U, p["task_id"], True, today().isoformat())
            st.rerun()

    wk = weekly_progress(tasks, today())
    c1, c2 = st.columns(2)
    with c1:
        metric_card("Tasks completed (7 days)", int(wk["tasks"].sum()))
    with c2:
        metric_card("Minutes studied (7 days)", int(wk["minutes"].sum()))
    fig = px.bar(wk, x="date", y="minutes", labels={"minutes": "Minutes completed"})
    fig.update_traces(marker_color="#0F766E")
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("7-day plan", expanded=False):
        if plan:
            st.dataframe(pd.DataFrame(plan).drop(columns="task_id"), hide_index=True, use_container_width=True)
        else:
            st.caption("No open tasks.")

    with st.expander("Add a task"):
        with st.form("add_task", clear_on_submit=True):
            title = st.text_input("Task *")
            c1, c2, c3 = st.columns(3)
            skill = c1.text_input("Skill (optional)")
            minutes = c2.number_input("Minutes", 5, 600, 45, 5)
            has_due = c3.checkbox("Has due date")
            due = st.date_input("Due date", value=today())
            if st.form_submit_button("Add task", type="primary"):
                d = {"title": title.strip(), "skill": skill.strip().lower(), "minutes": int(minutes),
                     "due_date": due.isoformat() if has_due else None, "is_demo": 0}
                errs = validate_task(d)
                if errs:
                    st.error(" ".join(errs))
                else:
                    db.insert("study_tasks", U, d)
                    st.rerun()

    st.subheader("Edit tasks")
    if tasks.empty:
        return
    view = tasks[["id", "title", "skill", "minutes", "due_date", "done"]].copy()
    view["due_date"] = pd.to_datetime(view["due_date"], errors="coerce").dt.date
    view["done"] = view["done"].astype(bool)
    edited = st.data_editor(view, hide_index=True, use_container_width=True, disabled=["id"], key="task_editor",
                            column_config={"due_date": st.column_config.DateColumn("Due"),
                                           "minutes": st.column_config.NumberColumn(min_value=5, max_value=600, step=5)})
    if st.button("Save task changes"):
        errors = 0
        for r in edited.to_dict("records"):
            due = None if pd.isna(r["due_date"]) else r["due_date"].isoformat()
            d = {"title": str(r["title"] or "").strip(), "minutes": int(r["minutes"] or 0)}
            if validate_task(d):
                errors += 1
                continue
            db.update("study_tasks", U, int(r["id"]), {**d, "skill": r["skill"], "due_date": due})
            was = bool(view.loc[view["id"] == r["id"], "done"].iloc[0])
            if bool(r["done"]) != was:
                db.set_task_done(U, int(r["id"]), bool(r["done"]), today().isoformat())
        st.warning(f"{errors} row(s) skipped (invalid title/minutes).") if errors else st.success("Saved.")
        st.rerun() if not errors else None
    del_id = st.selectbox("Delete a task", [None, *view["id"].tolist()], format_func=lambda x: "-" if x is None else f"#{x}")
    if del_id is not None and st.button("Delete task"):
        db.delete("study_tasks", U, int(del_id))
        st.rerun()
