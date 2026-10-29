"""Synthetic training data: jobs, jobseekers and simulated employer shortlisting.

The label (`shortlisted`) comes from a hidden rule that mimics employer behaviour, so a
model trained on it mostly learns that rule back. This is a teaching demo, NOT evidence
the model works on real hiring data.
"""

import math

import numpy as np
import pandas as pd

from core.features import pair_features

STATES = ["Lagos", "FCT", "Kano", "Oyo", "Rivers", "Kaduna", "Enugu", "Ogun"]
ROLES = {  # role: (core skills, optional skills, min years, min education)
    "Data Analyst": (["excel", "sql", "data_analysis"], ["power_bi", "python", "statistics", "communication", "data_visualization"], 1, "bsc"),
    "Junior Data Scientist": (["python", "statistics", "sql"], ["data_analysis", "machine_learning", "power_bi", "problem_solving"], 2, "bsc"),
    "M&E Assistant": (["excel", "data_analysis", "monitoring_evaluation"], ["statistics", "survey_tools", "english_writing", "project_management"], 1, "bsc"),
    "Data Entry Clerk": (["data_entry", "excel"], ["communication", "teamwork", "survey_tools"], 0, "secondary"),
    "Frontend Developer": (["web_development", "javascript"], ["graphic_design", "problem_solving", "teamwork"], 1, "ond"),
    "IT Support Technician": (["it_support", "networking"], ["customer_service", "problem_solving"], 0, "ond"),
    "Digital Marketing Officer": (["digital_marketing", "social_media", "content_writing"], ["graphic_design", "data_analysis", "communication"], 1, "ond"),
    "Graphic Designer": (["graphic_design"], ["social_media", "photography", "video_editing"], 0, "secondary"),
    "Bookkeeper": (["bookkeeping", "accounting_software", "excel"], ["financial_literacy", "communication"], 1, "ond"),
    "POS / Mobile Money Agent": (["mobile_money_ops", "customer_service"], ["financial_literacy", "sales"], 0, "secondary"),
    "Sales Representative": (["sales", "customer_service", "communication"], ["digital_marketing", "driving"], 0, "secondary"),
    "Customer Care Agent": (["customer_service", "communication"], ["english_writing", "problem_solving", "it_support"], 0, "secondary"),
    "Procurement Assistant": (["procurement", "inventory_management", "excel"], ["communication", "logistics"], 1, "ond"),
    "Farm Supervisor": (["agronomy", "irrigation"], ["post_harvest_handling", "teamwork", "agribusiness"], 1, "tvet"),
    "Poultry Farm Manager": (["poultry_management", "agribusiness"], ["bookkeeping", "teamwork"], 2, "tvet"),
    "Agric Extension Agent": (["extension_services", "agronomy", "communication"], ["driving", "english_writing"], 1, "ond"),
    "Aquaculture Technician": (["aquaculture"], ["post_harvest_handling", "agribusiness"], 0, "tvet"),
    "Solar PV Installer": (["solar_pv", "electrical_installation"], ["problem_solving", "driving"], 0, "tvet"),
    "Electrician": (["electrical_installation"], ["solar_pv", "teamwork"], 1, "tvet"),
    "Auto Mechanic": (["motor_mechanics"], ["welding", "customer_service"], 1, "tvet"),
    "Welder / Fabricator": (["welding"], ["carpentry", "teamwork"], 0, "tvet"),
    "Dispatch Rider / Logistics": (["logistics", "driving"], ["customer_service", "mobile_money_ops"], 0, "secondary"),
    "Warehouse Officer": (["warehouse_ops", "inventory_management"], ["excel", "logistics", "teamwork"], 1, "secondary"),
    "Community Health Worker": (["community_health", "first_aid", "communication"], ["data_entry", "english_writing"], 0, "tvet"),
    "Fashion Designer": (["fashion_design"], ["social_media", "sales", "photography"], 0, "secondary"),
    "Video Editor": (["video_editing"], ["photography", "graphic_design", "social_media"], 0, "secondary"),
    "Project Officer": (["project_management", "communication", "english_writing"], ["excel", "data_analysis", "monitoring_evaluation"], 2, "bsc"),
}
EDU_LEVELS = ["secondary", "tvet", "ond", "bsc", "msc"]


def _sigmoid(z):
    return 1 / (1 + math.exp(-z))


def generate(n_jobs=1500, n_cands=4000, seed=7):
    """Return (jobs, candidates, applications): two lists of dicts and a DataFrame."""
    rng = np.random.default_rng(seed)
    roles = list(ROLES)
    jobs = []
    for j in range(n_jobs):
        r = rng.choice(roles)
        core, opt, mexp, medu = ROLES[r]
        jobs.append(
            {
                "job_id": f"J{j:04d}",
                "title": r,
                "core_skills": list(core),
                "optional_skills": list(rng.choice(opt, size=rng.integers(1, len(opt) + 1), replace=False)),
                "min_experience": int(max(0, mexp + rng.integers(-1, 2))),
                "min_education": medu,
                "state": "Remote" if rng.random() < 0.12 else str(rng.choice(STATES)),
            }
        )
    cands = []
    for c in range(n_cands):
        r = rng.choice(roles)
        core, opt, mexp, medu = ROLES[r]
        skills = {s for s in core if rng.random() < 0.75} | {s for s in opt if rng.random() < 0.45}
        if rng.random() < 0.35:  # career switchers / mixed profiles
            skills |= {s for s in ROLES[rng.choice(roles)][0] if rng.random() < 0.5}
        skills |= {s for s in ["communication", "teamwork", "problem_solving"] if rng.random() < 0.3}
        floor = EDU_LEVELS.index(medu if medu in EDU_LEVELS else "tvet")
        cands.append(
            {
                "candidate_id": f"C{c:04d}",
                "background": r,
                "skills": sorted(skills),
                "years_experience": int(rng.integers(0, 6)),
                "education": EDU_LEVELS[int(np.clip(floor + rng.integers(-1, 2), 0, 4))],
                "state": str(rng.choice(STATES)),
                "signup_day": int(rng.integers(0, 60)),
            }
        )
    by_title = {}
    for job in jobs:
        by_title.setdefault(job["title"], []).append(job)
    rows = []
    for c in cands:  # each person applies to 4 jobs in their field + 4 random jobs
        picked = list(rng.choice(by_title[c["background"]], size=4)) + list(rng.choice(jobs, size=4))
        for j in picked:
            f = pair_features(c, j)
            # hidden "employer behaviour" the model must learn
            z = (
                -4.8
                + 5.5 * f["core_coverage"]
                + 1.2 * f["optional_coverage"]
                + 1.0 * f["exp_ok"]
                + 0.25 * np.clip(f["exp_gap"], -3, 3)
                + 1.2 * f["location_ok"]
                + 0.5 * (f["edu_gap"] >= 0)
                - 0.6 * (f["edu_gap"] >= 2)
            )
            rows.append(
                {
                    **f,
                    "candidate_id": c["candidate_id"],
                    "job_id": j["job_id"],
                    "signup_day": c["signup_day"],
                    "shortlisted": int(rng.random() < _sigmoid(z)),
                    "keyword_overlap": len(set(c["skills"]) & set(j["core_skills"] + j["optional_skills"])),
                }
            )
    return jobs, cands, pd.DataFrame(rows)


def make_applications(seed=7, n_jobs=1500, n_cands=4000):
    """Return only the applications DataFrame (what training needs).

    The default seed is 7, the notebook's seed, so we can check that the extraction
    reproduces the notebook's numbers exactly.
    """
    return generate(n_jobs=n_jobs, n_cands=n_cands, seed=seed)[2]
