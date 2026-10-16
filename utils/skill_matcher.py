"""
Skill Gap engine: compares a candidate's known skills against a target job's
required programming languages, producing Matched / Missing / Weak lists.

Kept modular so similarity-based (fuzzy/NLP) matching can replace the exact
match below without changing how callers use `compute_skill_gap`.
"""
from data.jobs_data import JOB_REQUIREMENTS


def compute_skill_gap(candidate_skills, target_job, weak_language_names=None):
    """
    candidate_skills: list[str] of skills detected from resume/profile
    target_job: str, must be a key in JOB_REQUIREMENTS
    weak_language_names: optional list[str] of languages the candidate listed
                          but scored poorly on in a past assessment.

    Returns dict: {"required": [...], "matched": [...], "missing": [...], "weak": [...]}
    """
    required = JOB_REQUIREMENTS.get(target_job, [])
    candidate_set = {s.strip().lower() for s in candidate_skills}
    weak_set = {s.strip().lower() for s in (weak_language_names or [])}

    matched, missing, weak = [], [], []
    for lang in required:
        if lang.lower() in candidate_set:
            if lang.lower() in weak_set:
                weak.append(lang)
            else:
                matched.append(lang)
        else:
            missing.append(lang)

    return {
        "required": required,
        "matched": matched,
        "missing": missing,
        "weak": weak,
    }
