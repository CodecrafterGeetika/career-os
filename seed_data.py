"""Demo data. Opportunities and tasks are ILLUSTRATIVE and flagged is_demo=1: they are not
official notices, and carry no URLs or real deadlines. Resources link to the home pages of
well-known free learning sites; availability should still be verified by the learner."""
from __future__ import annotations

from datetime import date, timedelta

import database as db

DEMO_NOTE = "DEMO DATA - illustrative only, not an official notice. Add real details from the official source."

_OPPS = [
    ("[DEMO] Backend Intern", "Example Tech Pvt Ltd", "Internship", "Remote", 21, 7.0, "cse,it", "python, sql, git"),
    ("[DEMO] Graduate Software Engineer", "Sample Systems", "Job", "Bengaluru", 35, 7.5, "cse,it,ece", "dsa, python, dbms, git"),
    ("[DEMO] Web Developer Intern", "Demo Studio", "Internship", "Hybrid", 14, 6.5, "", "web development, javascript, git"),
    ("[DEMO] Systems Engineer Trainee", "Placeholder Infra", "Job", "Pune", 45, 7.0, "cse,it", "operating systems, computer networks, linux, python"),
    ("[DEMO] Illustrative PSU Technical Exam", "Example Public Sector Unit", "Government Exam", "India", 60, 0, "cse,it,ece", "dsa, operating systems, dbms, computer networks, aptitude"),
    ("[DEMO] Illustrative State Services Exam", "Example Commission", "Government Exam", "India", 75, 0, "", "aptitude, mathematics"),
    ("[DEMO] GATE CSE (set your real date)", "Official GATE organising institute", "GATE", "India", 120, 0, "cse,it", "dsa, algorithms, operating systems, dbms, computer networks, digital logic, discrete mathematics"),
]

_TASKS = [
    ("Revise SQL joins", "sql", 2, 45), ("Solve 3 array problems", "dsa", 1, 60),
    ("Read OS scheduling chapter", "operating systems", 4, 50), ("Git branching practice", "git", 3, 30),
    ("Aptitude: percentages set", "aptitude", 5, 40),
]

_RESOURCES = [
    ("CS50x: Intro to Computer Science", "Harvard", "https://cs50.harvard.edu/x", "dsa", "Course"),
    ("CS50 Python", "Harvard", "https://cs50.harvard.edu/python", "python", "Course"),
    ("Python Tutorial (official docs)", "Python.org", "https://docs.python.org/3/tutorial/", "python", "Docs"),
    ("freeCodeCamp Curriculum", "freeCodeCamp", "https://www.freecodecamp.org/learn", "web development", "Course"),
    ("MDN Learn Web Development", "Mozilla", "https://developer.mozilla.org/en-US/docs/Learn", "web development", "Docs"),
    ("MDN JavaScript Guide", "Mozilla", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "javascript", "Docs"),
    ("SQLBolt interactive lessons", "SQLBolt", "https://sqlbolt.com", "sql", "Practice"),
    ("Pro Git (free book)", "git-scm.com", "https://git-scm.com/book", "git", "Book"),
    ("Visualgo algorithm visualisations", "VisuAlgo", "https://visualgo.net", "algorithms", "Interactive"),
    ("MIT OpenCourseWare", "MIT", "https://ocw.mit.edu", "algorithms", "Course"),
    ("The Missing Semester", "MIT CSAIL", "https://missing.csail.mit.edu", "linux", "Course"),
    ("Operating Systems: Three Easy Pieces", "Univ. of Wisconsin", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "operating systems", "Book"),
    ("NPTEL courses (search the subject)", "NPTEL", "https://nptel.ac.in", "dbms", "Course"),
    ("NPTEL courses (search the subject)", "NPTEL", "https://nptel.ac.in", "computer networks", "Course"),
    ("NPTEL courses (search the subject)", "NPTEL", "https://nptel.ac.in", "discrete mathematics", "Course"),
    ("Nand2Tetris", "nand2tetris.org", "https://www.nand2tetris.org", "digital logic", "Course"),
    ("Khan Academy Math", "Khan Academy", "https://www.khanacademy.org/math", "mathematics", "Course"),
    ("Khan Academy Math (arithmetic practice)", "Khan Academy", "https://www.khanacademy.org/math", "aptitude", "Practice"),
]


def seed_demo(user_id: int, path: str | None = None) -> bool:
    """Idempotent: seeds each part once, tracked in the meta table."""
    did = False
    if not db.get_meta("seeded_resources", path):
        for t, p, u, s, k in _RESOURCES:
            db.insert("resources", 0, {"title": t, "provider": p, "url": u, "skill": s, "kind": k}, path)
        db.set_meta("seeded_resources", "1", path)
        did = True
    key = f"seeded_user:{user_id}"
    if not db.get_meta(key, path):
        today = date.today()
        for t, org, kind, loc, days, cg, br, sk in _OPPS:
            db.insert("opportunities", user_id, {
                "title": t, "org": org, "kind": kind, "location": loc,
                "deadline": (today + timedelta(days=days)).isoformat(), "min_cgpa": cg, "branches": br,
                "required_skills": sk, "url": "", "notes": DEMO_NOTE, "is_demo": 1}, path)
        for t, sk, days, mins in _TASKS:
            db.insert("study_tasks", user_id, {"title": t, "skill": sk, "minutes": mins, "is_demo": 1,
                      "due_date": (today + timedelta(days=days)).isoformat()}, path)
        db.set_meta(key, "1", path)
        did = True
    return did
