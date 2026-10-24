from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["Dashboard", "Job and Internship Tracker", "Government Exams and GATE", "Career Readiness Radar",
         "Daily Study Planner", "Free Resources Library", "Profile and Settings"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DB", str(tmp_path / "smoke.db"))
    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=60).run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]
