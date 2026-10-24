"""Transparent rule-based scoring. Eligibility score (0-100):
  CGPA meets minimum  -> 30 points (30 if no minimum)
  Branch allowed      -> 20 points (20 if no branch restriction)
  Skills              -> 50 * (matched required skills / required skills) (50 if none required)
Labels: >=75 Strong match, >=50 Partial match, otherwise Low match."""
from __future__ import annotations

from collections import Counter

from utils.common import clean_num, clean_str, parse_list

SKILL_CATEGORIES = {
    "Programming": ["python", "java", "c++", "javascript"],
    "DSA and problem solving": ["dsa", "algorithms", "problem solving"],
    "CS fundamentals": ["operating systems", "computer networks", "dbms", "digital logic"],
    "Development tools": ["web development", "git", "sql", "linux"],
    "Aptitude and maths": ["aptitude", "mathematics", "discrete mathematics"],
    "Projects and communication": ["projects", "communication", "resume"],
}
ALL_SKILLS = sorted({s for v in SKILL_CATEGORIES.values() for s in v})
GATE_SUBJECTS = ["Engineering Mathematics", "Discrete Mathematics", "Digital Logic", "Computer Organization",
                 "Programming and Data Structures", "Algorithms", "Theory of Computation", "Compiler Design",
                 "Operating Systems", "Databases", "Computer Networks", "General Aptitude"]


def label_for(score: int) -> str:
    return "Strong match" if score >= 75 else "Partial match" if score >= 50 else "Low match"


def eligibility(profile: dict, opp: dict) -> dict:
    reasons: list[str] = []
    score = 0
    min_cgpa = clean_num(opp.get("min_cgpa"))
    cgpa = clean_num(profile.get("cgpa"))
    if cgpa >= min_cgpa:
        score += 30
        reasons.append("CGPA requirement met" if min_cgpa else "No CGPA requirement")
    else:
        reasons.append(f"CGPA {cgpa:.1f} is below the {min_cgpa:.1f} minimum")
    branches = parse_list(opp.get("branches"))
    branch = clean_str(profile.get("branch")).strip().lower()
    if not branches or "any" in branches or branch in branches:
        score += 20
        reasons.append("Branch eligible")
    else:
        reasons.append(f"Branch '{branch}' not in {', '.join(branches)}")
    required, have = parse_list(opp.get("required_skills")), set(parse_list(profile.get("skills")))
    gaps = [s for s in required if s not in have]
    if required:
        score += round(50 * (len(required) - len(gaps)) / len(required))
        reasons.append(f"Skills: {len(required) - len(gaps)}/{len(required)} matched")
    else:
        score += 50
    return {"score": score, "label": label_for(score), "gaps": gaps, "reasons": reasons}


def skill_gaps(profile: dict, opps: list[dict]) -> list[tuple[str, int]]:
    """Missing skills ranked by how many active opportunities need them."""
    counter: Counter = Counter()
    for o in opps:
        if clean_str(o.get("status")) == "Rejected":
            continue
        counter.update(eligibility(profile, o)["gaps"])
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def readiness(profile_skills) -> dict[str, int]:
    """Per category: percent of that category's listed skills the student has."""
    have = set(parse_list(profile_skills))
    return {cat: round(100 * len([s for s in sk if s in have]) / len(sk)) for cat, sk in SKILL_CATEGORIES.items()}
