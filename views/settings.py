import streamlit as st

import database as db
from utils.ai import ai_available, study_tips
from utils.common import parse_list
from utils.scoring import ALL_SKILLS, skill_gaps
from utils.ui import CURRENT_USER as U, header
from utils.validation import validate_profile


def render():
    header("Profile and Settings", "Your profile drives eligibility matches, skill gaps, and the radar.")
    p = db.get_profile(U)
    with st.form("profile"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", p["name"])
        branch = c2.text_input("Branch (e.g. cse, it, ece)", p["branch"])
        c3, c4, c5 = st.columns(3)
        cgpa = c3.number_input("CGPA", 0.0, 10.0, float(p["cgpa"]), 0.1)
        grad = c4.number_input("Graduation year", 2000, 2100, int(p["grad_year"]))
        hours = c5.number_input("Daily study hours", 0.5, 16.0, float(p["daily_hours"]), 0.5)
        have = parse_list(p["skills"])
        picked = st.multiselect("Skills you have", sorted(set(ALL_SKILLS) | set(have)), default=have)
        extra = st.text_input("Other skills (comma-separated)")
        role = st.text_input("Target role", p["target_role"])
        if st.form_submit_button("Save profile", type="primary"):
            data = {"name": name.strip(), "branch": branch.strip().lower(), "cgpa": float(cgpa), "grad_year": int(grad),
                    "daily_hours": float(hours), "skills": ", ".join(parse_list(", ".join([*picked, extra]))),
                    "target_role": role.strip()}
            errs = validate_profile(data)
            if errs:
                st.error(" ".join(errs))
            else:
                db.save_profile(U, data)
                st.success("Profile saved.")

    st.subheader("Data")
    st.download_button("Export opportunities (CSV)", db.list_opportunities(U).to_csv(index=False), "opportunities.csv")
    st.download_button("Export study tasks (CSV)", db.list_tasks(U).to_csv(index=False), "study_tasks.csv")
    if st.button("Remove all demo data"):
        db.clear_demo(U)
        st.rerun()

    st.subheader("Optional AI study tips")
    if ai_available():
        if st.button("Generate tips for my skill gaps"):
            gaps = [s for s, _ in skill_gaps(db.get_profile(U), db.list_opportunities(U).to_dict("records"))]
            with st.spinner("Thinking..."):
                st.markdown(study_tips(gaps[:6], p["target_role"]))
    else:
        st.caption("Not configured. Set the ANTHROPIC_API_KEY environment variable to enable. The app works fully without it.")
    st.caption("Storage: local SQLite file. This build has one profile and no login; SQLite does not isolate users.")
