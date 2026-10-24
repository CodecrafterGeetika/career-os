import plotly.express as px
import streamlit as st

import database as db
from utils.common import days_left
from utils.scoring import GATE_SUBJECTS
from utils.ui import CURRENT_USER as U, header
from utils.validation import validate_opportunity
from views._forms import opportunity_form
from views.tracker import scored_frame


def render():
    header("Government Exams and GATE", "Track exam dates you enter from official notices, and your GATE syllabus progress.")
    st.info("CareerOS does not fetch or verify notices. Always copy dates and eligibility from the official website.")
    profile = db.get_profile(U)
    df = scored_frame(profile, db.list_opportunities(U))
    df = df[df["kind"].isin(["Government Exam", "GATE"])] if not df.empty else df

    tab1, tab2 = st.tabs(["Exam tracker", "GATE syllabus progress"])
    with tab1:
        with st.expander("Add an exam"):
            ok, data, status = opportunity_form(["Government Exam", "GATE"], "add_exam")
            if ok:
                errs = validate_opportunity(data)
                if errs:
                    st.error(" ".join(errs))
                else:
                    oid = db.insert("opportunities", U, {**data, "is_demo": 0})
                    db.set_status(U, oid, status)
                    st.rerun()
        if df.empty:
            st.info("No exams tracked yet.")
        else:
            st.dataframe(df[["id", "title", "org", "kind", "status", "deadline", "days_left", "match", "match_label"]],
                         hide_index=True, use_container_width=True)
            ids = {int(r.id): f"#{r.id} {r.title}" for r in df.itertuples()}
            oid = st.selectbox("Update status", list(ids), format_func=ids.get)
            new = st.selectbox("New status", db.STATUSES)
            if st.button("Update status"):
                db.set_status(U, oid, new)
                st.rerun()
    with tab2:
        gate = df[df["kind"] == "GATE"] if not df.empty else df
        if not gate.empty:
            dl = days_left(gate.iloc[0]["deadline"])
            if dl is not None:
                st.metric("Days to the date you entered for GATE", dl)
        prog = db.get_gate_progress(U)
        cols = st.columns(2)
        new = {}
        for i, s in enumerate(GATE_SUBJECTS):
            new[s] = cols[i % 2].slider(s, 0, 100, int(prog.get(s, 0)), 5, key=f"gate_{s}")
        if st.button("Save GATE progress", type="primary"):
            for s, v in new.items():
                db.set_gate_progress(U, s, v)
            st.success("Saved.")
        fig = px.bar(x=list(new.values()), y=list(new.keys()), orientation="h", range_x=[0, 100],
                     labels={"x": "Self-assessed % complete", "y": ""})
        fig.update_traces(marker_color="#0F766E")
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Overall: {sum(new.values()) / len(new):.0f}% (simple average of your own ratings)")
