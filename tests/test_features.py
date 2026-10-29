import pytest

from core.features import EDU, FEATURES, pair_features, skill_vector
from core.taxonomy import SKILLS

CAND = {"skills": ["excel", "sql"], "years_experience": 3, "education": "bsc", "state": "Lagos"}
JOB = {
    "core_skills": ["excel", "sql", "data_analysis"],
    "optional_skills": ["python", "power_bi"],
    "min_experience": 2,
    "min_education": "bsc",
    "state": "Lagos",
}


def test_known_values_for_a_hand_made_pair():
    f = pair_features(CAND, JOB)
    assert f["core_coverage"] == pytest.approx(2 / 3)  # has 2 of 3 core skills
    assert f["optional_coverage"] == 0  # has neither optional skill
    assert f["n_core_missing"] == 1  # data_analysis
    # cosine of {excel, sql} vs 5 job skills = 2 / sqrt(2 * 5)
    assert f["cosine_sim"] == pytest.approx(2 / 10**0.5, abs=1e-5)
    assert f["exp_gap"] == 1
    assert f["exp_ok"] == 1
    assert f["edu_gap"] == 0
    assert f["location_ok"] == 1
    assert f["n_candidate_skills"] == 2


def test_feature_names_match_the_list_the_model_is_trained_on():
    # Guards against training/serving skew: if someone adds or renames a feature in
    # pair_features but not in FEATURES (or the reverse), this fails.
    assert set(pair_features(CAND, JOB)) == set(FEATURES)


def test_remote_job_is_ok_from_any_state():
    assert pair_features(CAND, {**JOB, "state": "Remote"})["location_ok"] == 1


def test_different_state_is_not_ok():
    assert pair_features(CAND, {**JOB, "state": "Kano"})["location_ok"] == 0


def test_experience_shortfall_is_negative_and_flagged():
    f = pair_features({**CAND, "years_experience": 0}, JOB)
    assert f["exp_gap"] == -2
    assert f["exp_ok"] == 0


def test_education_gap_sign():
    assert pair_features({**CAND, "education": "secondary"}, JOB)["edu_gap"] == -2
    assert pair_features({**CAND, "education": "msc"}, {**JOB, "min_education": "tvet"})["edu_gap"] == 2


def test_ond_and_tvet_are_the_same_rung():
    assert EDU["ond"] == EDU["tvet"]


def test_job_with_no_optional_skills_does_not_divide_by_zero():
    f = pair_features(CAND, {**JOB, "optional_skills": []})
    assert f["optional_coverage"] == 0


def test_candidate_with_no_skills_does_not_crash():
    f = pair_features({**CAND, "skills": []}, JOB)
    assert f["core_coverage"] == 0
    assert f["cosine_sim"] == 0


def test_skill_vector_has_unit_length_or_is_zero():
    assert len(skill_vector([])) == len(SKILLS)
    assert skill_vector([]).sum() == 0
    assert (skill_vector(["excel", "sql", "python"]) ** 2).sum() == pytest.approx(1.0, abs=1e-6)
