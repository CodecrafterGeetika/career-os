from datetime import date, timedelta

import pytest

import database as db
from seed_data import seed_demo
from utils.planner import build_plan, weekly_progress
from utils.scoring import eligibility, readiness, skill_gaps
from utils.validation import validate_opportunity, validate_profile, validate_task


@pytest.fixture
def path(tmp_path):
    p = str(tmp_path / "t.db")
    db.init_db(p)
    return p


PROFILE = {"cgpa": 7.5, "branch": "cse", "skills": "python, git"}


def test_eligibility_full_and_partial():
    full = eligibility(PROFILE, {"min_cgpa": 7, "branches": "cse,it", "required_skills": "python, git"})
    assert full["score"] == 100 and full["gaps"] == []
    part = eligibility(PROFILE, {"min_cgpa": 8, "branches": "ece", "required_skills": "python, sql"})
    assert part["score"] == 25 and part["gaps"] == ["sql"] and part["label"] == "Low match"


def test_eligibility_handles_blank_fields():
    assert eligibility(PROFILE, {"min_cgpa": None, "branches": float("nan"), "required_skills": None})["score"] == 100


def test_skill_gaps_ranked_and_skip_rejected():
    opps = [{"required_skills": "sql, dsa", "status": "Saved"}, {"required_skills": "sql", "status": "Applied"},
            {"required_skills": "linux", "status": "Rejected"}]
    assert skill_gaps(PROFILE, opps) == [("sql", 2), ("dsa", 1)]


def test_readiness():
    r = readiness("python, java, c++, javascript")
    assert r["Programming"] == 100 and r["Aptitude and maths"] == 0


def test_plan_orders_by_deadline_and_splits():
    today = date(2026, 1, 1)
    tasks = [{"id": 1, "title": "B", "minutes": 90, "due_date": "2026-01-05", "done": 0},
             {"id": 2, "title": "A", "minutes": 60, "due_date": "2026-01-02", "done": 0},
             {"id": 3, "title": "done", "minutes": 60, "due_date": None, "done": 1}]
    plan = build_plan(tasks, 1.5, today)
    assert plan[0]["task_id"] == 2 and sum(p["minutes"] for p in plan) == 150
    assert all(p["minutes"] <= 90 for p in plan)
    assert {p["task_id"] for p in plan} == {1, 2}
    assert build_plan(tasks, 0, today) == []


def test_plan_flags_late():
    plan = build_plan([{"id": 1, "title": "X", "minutes": 120, "due_date": "2026-01-01", "done": 0}], 1, date(2026, 1, 1))
    assert [p["late"] for p in plan] == [False, True]


def test_validation():
    assert validate_opportunity({"title": "", "kind": "Job"})
    assert not validate_opportunity({"title": "x", "kind": "Job", "min_cgpa": 7, "url": "https://example.com"})
    assert validate_opportunity({"title": "x", "kind": "Job", "url": "javascript:alert(1)"})
    assert validate_profile({"name": "a", "cgpa": 11, "daily_hours": 2, "grad_year": 2027})
    assert validate_task({"title": "t", "minutes": 1})


def test_db_crud_and_isolation(path):
    a = db.insert("opportunities", 1, {"title": "T", "kind": "Job"}, path)
    db.set_status(1, a, "Applied", "2026-01-01", path)
    assert db.list_opportunities(1, path).iloc[0]["status"] == "Applied"
    db.update("opportunities", 2, a, {"title": "hacked"}, path)  # other user cannot modify
    assert db.list_opportunities(1, path).iloc[0]["title"] == "T"
    with pytest.raises(ValueError):
        db.set_status(2, a, "Saved", None, path)
    with pytest.raises(ValueError):
        db.set_status(1, a, "Bogus", None, path)
    assert db.list_opportunities(2, path).empty
    db.delete("opportunities", 1, a, path)
    assert db.list_opportunities(1, path).empty


def test_sql_injection_text_is_stored_literally(path):
    evil = "x'); DROP TABLE opportunities;--"
    db.insert("opportunities", 1, {"title": evil, "kind": "Job"}, path)
    assert db.list_opportunities(1, path).iloc[0]["title"] == evil


def test_profile_roundtrip_and_defaults(path):
    assert db.get_profile(1, path)["branch"] == "cse"
    db.save_profile(1, {"cgpa": 8.2, "skills": "sql"}, path)
    assert db.get_profile(1, path)["cgpa"] == 8.2


def test_seed_idempotent_and_weekly_progress(path):
    assert seed_demo(1, path) is True and seed_demo(1, path) is False
    assert (db.list_opportunities(1, path)["is_demo"] == 1).all()
    t = db.list_tasks(1, path)
    db.set_task_done(1, int(t.iloc[0]["id"]), True, date.today().isoformat(), path)
    wk = weekly_progress(db.list_tasks(1, path), date.today())
    assert len(wk) == 7 and wk["tasks"].sum() == 1
    db.clear_demo(1, path)
    assert db.list_opportunities(1, path).empty
    assert not db.list_resources(1, path).empty


def test_gate_progress_clamped(path):
    db.set_gate_progress(1, "Algorithms", 150, path)
    assert db.get_gate_progress(1, path)["Algorithms"] == 100
