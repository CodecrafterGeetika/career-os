"""CareerOS CSE - career preparation workspace for CSE students."""
import streamlit as st

import database as db
from seed_data import seed_demo
from utils.ui import CURRENT_USER, inject_css
from views import dashboard, exams, planner, radar, resources, settings, tracker

st.set_page_config(page_title="CareerOS CSE", page_icon="🧭", layout="wide")

PAGES = {
    "Dashboard": dashboard,
    "Job and Internship Tracker": tracker,
    "Government Exams and GATE": exams,
    "Career Readiness Radar": radar,
    "Daily Study Planner": planner,
    "Free Resources Library": resources,
    "Profile and Settings": settings,
}


@st.cache_resource
def _bootstrap(path: str) -> bool:
    db.init_db(path)
    seed_demo(CURRENT_USER, path)
    return True


def main() -> None:
    _bootstrap(db.db_path())
    inject_css()
    st.sidebar.markdown("### 🧭 CareerOS CSE")
    st.sidebar.caption("Plan. Prepare. Apply.")
    choice = st.sidebar.radio("Navigate", list(PAGES), label_visibility="collapsed")
    try:
        PAGES[choice].render()
    except Exception as exc:  # keep the app alive and show a readable message
        st.error(f"Something went wrong on this page: {exc}")


main()
