"""Feature engineering for a (candidate, job) pair.

`pair_features` is the ONE function used by both training and serving. If training and
serving ever computed features differently, the model would look good offline and fail
live: training/serving skew.
"""

import numpy as np

from core.taxonomy import IDX, SKILLS

FEATURES = [
    "core_coverage",
    "optional_coverage",
    "n_core_missing",
    "cosine_sim",
    "exp_gap",
    "exp_ok",
    "edu_gap",
    "location_ok",
    "n_candidate_skills",
]

# Education levels as ordered numbers (ond and tvet count as the same rung).
EDU = {"secondary": 0, "tvet": 1, "ond": 1, "hnd": 2, "bsc": 2, "msc": 3}
EDU_LABEL = {
    "secondary": "Secondary (SSCE)",
    "tvet": "TVET / trade certificate",
    "ond": "OND / Diploma",
    "hnd": "HND",
    "bsc": "Bachelor's degree",
    "msc": "Master's or higher",
}


def skill_vector(skills):
    """One-hot vector over the taxonomy, scaled to unit length (so dot product = cosine)."""
    v = np.zeros(len(SKILLS), dtype=np.float32)
    for s in skills:
        v[IDX[s]] = 1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def pair_features(cand, job):
    """Turn one candidate and one job into the numbers the model sees."""
    cs, core, opt = set(cand["skills"]), set(job["core_skills"]), set(job["optional_skills"])
    exp_gap = cand["years_experience"] - job["min_experience"]
    return {
        "core_coverage": len(cs & core) / max(len(core), 1),
        "optional_coverage": len(cs & opt) / max(len(opt), 1),
        "n_core_missing": len(core - cs),
        "cosine_sim": float(skill_vector(cs) @ skill_vector(core | opt)),
        "exp_gap": exp_gap,
        "exp_ok": int(exp_gap >= 0),
        "edu_gap": EDU.get(cand["education"], 0) - EDU.get(job["min_education"], 0),
        "location_ok": int(job["state"] == "Remote" or job["state"] == cand["state"]),
        "n_candidate_skills": len(cs),
    }
