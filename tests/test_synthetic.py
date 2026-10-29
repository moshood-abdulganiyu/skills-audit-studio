from pandas.testing import assert_frame_equal

from core.features import FEATURES
from core.synthetic import make_applications


def test_same_seed_gives_identical_data():
    a = make_applications(seed=1, n_jobs=300, n_cands=50)
    b = make_applications(seed=1, n_jobs=300, n_cands=50)
    assert_frame_equal(a, b)


def test_different_seed_gives_different_data():
    a = make_applications(seed=1, n_jobs=300, n_cands=50)
    b = make_applications(seed=2, n_jobs=300, n_cands=50)
    assert not a.equals(b)


def test_has_the_columns_training_needs():
    apps = make_applications(seed=0, n_jobs=300, n_cands=50)
    assert set(FEATURES) <= set(apps.columns)
    assert {"candidate_id", "job_id", "signup_day", "shortlisted", "keyword_overlap"} <= set(apps.columns)
    assert len(apps) == 50 * 8  # every candidate applies to 8 jobs
    assert set(apps["shortlisted"]) <= {0, 1}
