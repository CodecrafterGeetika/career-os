import streamlit as st

import database as db
from utils.scoring import ALL_SKILLS
from utils.ui import CURRENT_USER as U, header
from utils.validation import valid_url


def render():
    header("Free Resources Library", "Free learning links mapped to skills. Check each site for current availability.")
    df = db.list_resources(U)
    c1, c2 = st.columns(2)
    skills = c1.multiselect("Skill", sorted(df["skill"].unique()))
    q = c2.text_input("Search")
    f = df
    if skills:
        f = f[f["skill"].isin(skills)]
    if q:
        f = f[f["title"].str.contains(q, case=False, na=False) | f["provider"].str.contains(q, case=False, na=False)]
    if f.empty:
        st.info("No resources match. Add your own below.")
    for r in f.itertuples():
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f"**{r.title}**  \n{r.provider} | {r.kind} | skill: `{r.skill}`")
            b.link_button("Open", r.url, use_container_width=True)
    with st.expander("Add a resource"):
        with st.form("add_res", clear_on_submit=True):
            title = st.text_input("Title *")
            provider = st.text_input("Provider")
            url = st.text_input("URL * (https://...)")
            skill = st.selectbox("Skill", ALL_SKILLS)
            kind = st.selectbox("Kind", ["Course", "Book", "Docs", "Practice", "Video", "Interactive"])
            if st.form_submit_button("Save resource", type="primary"):
                if not title.strip() or not url.strip() or not valid_url(url):
                    st.error("Title and a valid http(s) URL are required.")
                else:
                    db.insert("resources", U, {"title": title.strip(), "provider": provider.strip(),
                                               "url": url.strip(), "skill": skill, "kind": kind})
                    st.rerun()
