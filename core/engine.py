"""Inference engine and the skills audit.

`InferenceEngine` loads one saved model version and scores (candidate, job) pairs.
`skill_audit` is the full pipeline: parse both documents -> features -> score -> explain.
No display code lives here: the notebook, API and tests all call these functions.
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd

from core.features import EDU, FEATURES, pair_features
from core.parsing import parse_job, parse_resume
from core.taxonomy import SKILLS, course_for


class InferenceEngine:
    """Loads a saved model folder once and serves predictions, like the API will.

    Only load model folders from this repo: joblib files are pickles, and loading an
    untrusted pickle can run arbitrary code.
    """

    def __init__(self, folder):
        folder = Path(folder)
        self.model = joblib.load(folder / "model.joblib")
        with open(folder / "model_meta.json", encoding="utf-8") as f:
            self.meta = json.load(f)
        # Explicit errors instead of `assert`, which Python can strip out with -O.
        if self.meta["features"] != FEATURES:
            raise ValueError("feature mismatch: retrain or update features")
        if self.meta["skills"] != SKILLS:
            raise ValueError("taxonomy changed since training: retrain")

    def score(self, cand, job):
        row = pd.DataFrame([pair_features(cand, job)])[FEATURES]
        return float(self.model.predict_proba(row)[0, 1])

    def lifts(self, cand, job, missing):
        """Counterfactual: 'what if this person had skill X?', re-scored by the same model."""
        base = self.score(cand, job)
        out = []
        for s in missing:
            new = self.score({**cand, "skills": sorted(set(cand["skills"]) | {s})}, job)
            out.append(
                {"skill": s, "score_after": round(new, 3), "lift": round(new - base, 3), "course": course_for(s)}
            )
        return sorted(out, key=lambda d: -d["lift"])


def verdict(score):
    """Turn a 0-1 score into a plain-language label."""
    if score >= 0.7:
        return "Strong match"
    if score >= 0.4:
        return "Moderate match"
    return "Weak match"


def skill_audit(engine, resume_text, jd_text, state_override=None, resume_name="resume"):
    """Score one resume against one job description and explain the gaps."""
    t0 = time.perf_counter()
    cand, job = parse_resume(resume_text, resume_name), parse_job(jd_text)
    if state_override:
        cand["state"], cand["state_found"] = state_override, True
    if job["remote_ok"] and job["state"] != "Remote":
        job_for_model = {**job, "state": cand["state"] if cand["state"] != "Unknown" else job["state"]}
    else:
        job_for_model = job
    score = engine.score(cand, job_for_model)
    cs = set(cand["skills"])
    missing_core = [s for s in job["core_skills"] if s not in cs]
    missing_opt = [s for s in job["optional_skills"] if s not in cs]
    lifts = [x for x in engine.lifts(cand, job_for_model, missing_core + missing_opt) if x["lift"] >= 0.005]
    req = job["core_skills"] + job["optional_skills"]
    ms = (time.perf_counter() - t0) * 1000
    remote_note = " (remote OK)" if job["remote_ok"] and job["state"] != "Remote" else ""
    return {
        "resume": resume_name,
        "candidate_name": cand["name"],
        "job_title": job["title"],
        "match_score": round(score, 3),
        "verdict": verdict(score),
        "keyword_overlap": round(len(cs & set(req)) / max(len(req), 1), 3),
        "requirements": [
            {
                "skill": s,
                "type": "Required" if s in job["core_skills"] else "Nice to have",
                "status": "Has" if s in cs else "Missing",
                "evidence": cand["evidence"].get(s, ""),
            }
            for s in req
        ],
        "missing_core": missing_core,
        "missing_optional": missing_opt,
        "extra_skills": sorted(cs - set(req)),
        "unrecognised_skills": cand["unknown_skills"],
        "checks": {
            "experience": {
                "candidate": cand["years_experience"],
                "required": job["min_experience"],
                "ok": cand["years_experience"] >= job["min_experience"],
                "note": cand["years_source"],
            },
            "education": {
                "candidate": cand["education"],
                "required": job["min_education"],
                "ok": EDU[cand["education"]] >= EDU[job["min_education"]],
                "note": "" if cand["education_found"] else "not found in resume (assumed secondary)",
            },
            "location": {
                "candidate": cand["state"],
                "required": job["state"] + remote_note,
                "ok": bool(job_for_model["state"] == "Remote" or job_for_model["state"] == cand["state"]),
                "note": "" if cand["state_found"] else "state not found in resume: set it manually",
            },
        },
        "priority_skills": lifts[:5],
        "latency_ms": round(ms, 1),
        "model_version": engine.meta["version"],
    }
