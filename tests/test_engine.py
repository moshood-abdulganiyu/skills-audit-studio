import json
from pathlib import Path

import joblib
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier

from core.engine import InferenceEngine, skill_audit, verdict
from core.features import FEATURES
from core.synthetic import make_applications
from core.taxonomy import SKILLS

DATA = Path(__file__).parent / "data"


def make_model_folder(folder, features=None, skills=None):
    """Train a tiny model and save it the way a real version folder will look."""
    apps = make_applications(seed=0, n_jobs=300, n_cands=300)
    model = HistGradientBoostingClassifier(max_iter=20, random_state=0)
    model.fit(apps[FEATURES], apps["shortlisted"])
    joblib.dump(model, folder / "model.joblib")
    meta = {"version": "test-v0", "features": features or FEATURES, "skills": skills or SKILLS}
    (folder / "model_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return folder


def test_audit_report_has_the_expected_shape(tmp_path):
    engine = InferenceEngine(make_model_folder(tmp_path))
    jd = (DATA / "job_data_analyst.txt").read_text(encoding="utf-8")
    resume = (DATA / "amina_bello.txt").read_text(encoding="utf-8")

    report = skill_audit(engine, resume, jd, resume_name="amina_bello.docx")

    assert report["model_version"] == "test-v0"
    assert report["candidate_name"] == "Amina Bello"
    assert 0 <= report["match_score"] <= 1
    assert report["verdict"] == verdict(report["match_score"])
    assert report["missing_core"] == ["python"]
    assert set(report["checks"]) == {"experience", "education", "location"}
    lifts = [p["lift"] for p in report["priority_skills"]]
    assert lifts == sorted(lifts, reverse=True)  # biggest gain first
    assert all(lift >= 0.005 for lift in lifts)  # tiny effects are filtered out


def test_state_override_changes_the_location_check(tmp_path):
    engine = InferenceEngine(make_model_folder(tmp_path))
    jd = (DATA / "job_data_analyst.txt").read_text(encoding="utf-8")
    resume = (DATA / "amina_bello.txt").read_text(encoding="utf-8")

    report = skill_audit(engine, resume, jd, state_override="Kano")

    assert report["checks"]["location"]["candidate"] == "Kano"
    assert report["checks"]["location"]["ok"] is False


def test_engine_refuses_a_model_trained_on_different_features(tmp_path):
    folder = make_model_folder(tmp_path, features=list(reversed(FEATURES)))
    with pytest.raises(ValueError, match="feature mismatch"):
        InferenceEngine(folder)


def test_engine_refuses_a_model_trained_on_a_different_taxonomy(tmp_path):
    folder = make_model_folder(tmp_path, skills=SKILLS[:-1])
    with pytest.raises(ValueError, match="taxonomy changed"):
        InferenceEngine(folder)


def test_verdict_thresholds():
    assert verdict(0.7) == "Strong match"
    assert verdict(0.699) == "Moderate match"
    assert verdict(0.4) == "Moderate match"
    assert verdict(0.399) == "Weak match"
