from pathlib import Path

from core.parsing import (
    find_education,
    find_skills,
    find_state,
    parse_job,
    parse_resume,
    years_from_ranges,
)

DATA = Path(__file__).parent / "data"


def read(name):
    return (DATA / name).read_text(encoding="utf-8")


# --- skills --------------------------------------------------------------------------------


def test_synonyms_map_to_canonical_skills():
    assert set(find_skills("MS Excel, MySQL")) == {"excel", "sql"}


def test_skill_evidence_records_the_phrase_that_matched():
    assert find_skills("I use pivot tables daily")["excel"] == "pivot tables"


def test_matching_respects_word_boundaries():
    # 'sage' sits inside 'message' and 'react' inside 'reacted'; neither is a skill here.
    assert find_skills("The message was sent and the team reacted") == {}


def test_matching_is_case_insensitive():
    assert "power_bi" in find_skills("POWER BI and Tableau")


# --- resumes -------------------------------------------------------------------------------


def test_resume_without_a_skills_section_does_not_crash():
    text = "Jane Doe\nLagos\n\nI worked as a data analyst using MySQL for three years."
    cand = parse_resume(text)
    assert {"sql", "data_analysis"} <= set(cand["skills"])
    assert cand["years_experience"] == 0
    assert cand["years_source"].startswith("not found")


def test_resume_with_almost_nothing_still_returns_the_full_shape():
    cand = parse_resume("Just a name")
    assert cand["skills"] == []
    assert cand["education"] == "secondary" and cand["education_found"] is False
    assert cand["state"] == "Unknown" and cand["state_found"] is False


def test_sample_resume_is_parsed_correctly():
    cand = parse_resume(read("amina_bello.txt"), "amina_bello.docx")
    assert cand["name"] == "Amina Bello"
    assert cand["state"] == "Lagos"
    assert cand["education"] == "bsc"
    assert cand["years_experience"] == 3 and cand["years_source"] == "stated in resume"
    assert {"excel", "sql", "data_visualization", "survey_tools", "monitoring_evaluation"} <= set(cand["skills"])
    assert "python" not in cand["skills"]
    assert cand["unknown_skills"] == ["Prompt engineering"]


# --- job descriptions ----------------------------------------------------------------------


def test_sample_job_splits_required_from_nice_to_have():
    job = parse_job(read("job_data_analyst.txt"))
    assert job["core_skills"] == ["data_analysis", "excel", "python", "sql"]
    assert {"power_bi", "statistics", "monitoring_evaluation"} <= set(job["optional_skills"])
    assert job["min_experience"] == 2
    assert job["min_education"] == "bsc"
    assert job["state"] == "Lagos"


def test_degree_lines_are_not_mistaken_for_skills():
    job = parse_job("Requirements\n- Degree in Statistics\n- SQL\n")
    assert job["core_skills"] == ["sql"]


# --- dates, education, location ------------------------------------------------------------


def test_overlapping_roles_are_counted_once():
    total, n_ranges = years_from_ranges("2020 - 2022 and 2021 - 2023", current_year=2026)
    assert (total, n_ranges) == (3, 2)


def test_present_means_the_current_year():
    assert years_from_ranges("2024 - Present", current_year=2026) == (2, 1)


def test_ranges_ending_in_the_future_are_ignored():
    assert years_from_ranges("2030 - 2035", current_year=2026) == (0, 0)


def test_education_picks_highest_or_lowest_as_asked():
    text = "OND in Accounting, then a Bachelor's degree"
    assert find_education(text, "max") == "bsc"
    assert find_education(text, "min") == "ond"


def test_hnd_is_not_read_as_ond():
    assert find_education("HND Statistics, Institute of Management") == "hnd"


def test_state_found_from_a_city_name():
    assert find_state("Ikeja, Lagos") == "Lagos"
    assert find_state("Abuja") == "FCT"
    assert find_state("No place mentioned here") is None
