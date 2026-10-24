# CareerOS CSE

A Streamlit workspace for CSE students: track jobs and internships, government exams and GATE, see transparent eligibility matches and skill gaps, get a daily study plan, and find free learning resources.

**Demo data:** the first launch loads illustrative opportunities and tasks tagged `[DEMO]`. They are not official notices, have no URLs, and their dates are placeholders. Remove them in *Profile and Settings*. Resource links point to home pages of well-known free sites; check availability yourself. CareerOS never fetches or verifies recruitment notices: copy dates and eligibility from official sources.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q                # run tests
```

The database is created automatically at `data/careeros.db` (override with `CAREEROS_DB=/path/file.db`).

## How scoring works
- **Eligibility (0-100):** CGPA meets minimum = 30, branch allowed = 20, skills = 50 x matched/required. 75+ strong, 50+ partial.
- **Skill gaps:** required skills you lack, ranked by how many active (non-rejected) opportunities need them, each linked to resources with the same skill tag.
- **Radar:** per category, the share of listed skills you have.
- **Planner:** open tasks sorted by due date then length, packed into your daily hours (tasks can split across days; chunks after the due date are flagged).

## Optional AI tips
`pip install anthropic`, then set `ANTHROPIC_API_KEY` (env var, or Streamlit secrets on Cloud). Only skill names are sent. Everything else works without it.

## Security and multi-user notes
- All SQL is parameterized; table/column names are whitelisted; inputs are validated; user text injected into HTML is escaped.
- This release has **one local profile and no login**. SQLite does not provide multi-user isolation. Every table has a `user_id` column and all queries filter by it, which is the groundwork, not the protection.
- Path to Supabase: add Supabase Auth, create the same tables in Postgres, enable row-level security with policies like `user_id = auth.uid()`, and reimplement the functions in `database.py` (same signatures) with `supabase-py` or `psycopg`. Put keys in Streamlit secrets, never in git.

## Push to GitHub
```bash
git init
git add .
git commit -m "CareerOS CSE initial release"
git branch -M main
git remote add origin https://github.com/<your-username>/careeros-cse.git
git push -u origin main
```
Create the empty `careeros-cse` repository on github.com first.

## Deploy on Streamlit Community Cloud
1. Go to share.streamlit.io and sign in with GitHub.
2. Click **Create app**, choose your repository, branch `main`, main file `app.py`.
3. Optional: under **Advanced settings > Secrets**, add `ANTHROPIC_API_KEY = "..."`.
4. Deploy. **Caution:** Community Cloud's filesystem is not persistent, so the SQLite file can reset on restart, and all visitors would share one profile. Use it for demos; move to Supabase with auth before real multi-user use.

## Structure
`app.py` (navigation) | `database.py` | `seed_data.py` | `views/` (one file per page) | `utils/` (scoring, planner, validation, UI, optional AI) | `tests/` | `.streamlit/config.toml`
