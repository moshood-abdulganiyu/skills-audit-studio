"""Parse resumes and job descriptions into structured dicts.

Everything here is plain text in, dict out: no files, no models, no display code.
"""

import re
from datetime import date

from core.features import EDU
from core.taxonomy import PHRASES

HEADER_WORDS = ["summary", "profile", "objective", "experience", "work experience", "employment", "work history",
                "professional experience", "education", "academic", "skills", "key skills", "technical skills",
                "core competencies", "competencies", "tools", "certifications", "certificates", "training", "projects",
                "requirements", "qualifications", "responsibilities", "key responsibilities", "duties", "about",
                "nice to have", "preferred", "desirable", "what you will need", "what you'll need", "who you are",
                "what we offer", "benefits", "how to apply", "languages", "referees", "references", "interests",
                "location", "job title", "role", "position"]
NG_STATES = ["Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Delta",
             "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
             "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
             "Taraba", "Yobe", "Zamfara", "FCT"]
STATE_ALIASES = {"abuja": "FCT", "fct": "FCT", "ikeja": "Lagos", "lekki": "Lagos", "yaba": "Lagos", "victoria island": "Lagos",
                 "port harcourt": "Rivers", "ibadan": "Oyo", "abeokuta": "Ogun", "zaria": "Kaduna", "nsukka": "Enugu"}
STATE_ALIASES.update({s.lower(): s for s in NG_STATES if s != "Niger"})   # 'Niger' is ambiguous (Niger Delta, Niger Republic)


def _clean(s):
    return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#&./\- ]", " ", s.lower())) + " "


def find_skills(text):
    # -> {canonical_skill: phrase_found}. Longest phrases first so 'power bi' wins over 'bi'.
    t, found = _clean(text), {}
    for phrase, skill in PHRASES.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", t):
            found.setdefault(skill, phrase)
    return found


def is_header(line):
    if line.lstrip()[:1] in "-•*–·▪>":             # bullet points are content, not headers
        return False
    s = line.strip().strip("#|").strip()
    if not s or len(s.split()) > 6:
        return False
    low = s.lower().rstrip(":").strip()
    if any(low == h or low.startswith(h + " ") or (len(low.split()) <= 3 and low.endswith(" " + h)) for h in HEADER_WORDS):
        return True
    return s.endswith(":") or (s.isupper() and len(s) >= 6 and low not in PHRASES)


def split_sections(text):
    # -> list of (header, [lines]); 'Skills: Excel, SQL' is split into header + content
    sections, cur = [], ("top", [])
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z' &/]{3,40}):\s*(.+)$", line)
        if m and is_header(m.group(1) + ":"):
            sections.append(cur)
            cur = (m.group(1).lower(), [m.group(2)])
        elif is_header(line):
            sections.append(cur)
            cur = (line.lower().strip(" :•*-#"), [])
        else:
            cur[1].append(line)
    sections.append(cur)
    return [s for s in sections if s[1] or s[0] != "top"]


def find_state(text):
    t = _clean(text)
    hits = [(m.start(), st) for a, st in STATE_ALIASES.items()
            for m in [re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", t)] if m]
    return min(hits)[1] if hits else None

_EDU_PATTERNS = [  # (level, regex)  'HND' is removed before testing OND/Diploma
    ("msc", r"\b(master'?s?|m\.?\s?sc|mba|m\.?\s?eng|mphil|ph\.?\s?d|doctorate)\b"),
    ("bsc", r"\b(bachelor'?s?|b\.?\s?sc|b\.?\s?eng|b\.?\s?tech|first degree|university degree|degree in|graduate degree)\b"),
    ("hnd", r"\b(hnd|higher national diploma)\b"),
    ("ond", r"\b(ond|national diploma|diploma)\b"),
    ("tvet", r"\b(nabteb|trade test|tvet|vocational|technical certificate|city\s?&\s?guilds|craft certificate)\b"),
    ("secondary", r"\b(ssce|waec|neco|secondary school|o'?\s?level)\b"),
]
def find_education(text, pick="max"):
    t = text.lower()
    levels = []
    for lvl, pat in _EDU_PATTERNS:
        if lvl == "ond":
            t2 = re.sub(_EDU_PATTERNS[2][1], " ", t)
            if re.search(pat, t2):
                levels.append(lvl)
        elif re.search(pat, t):
            levels.append(lvl)
    if not levels:
        return None
    return (max if pick == "max" else min)(levels, key=lambda level: EDU[level])

_RANGE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|date|now)", re.I)
_YEARS_STATED = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:\w+\s+){0,2}experience", re.I)


def years_from_ranges(text, current_year=None):
    """Total years covered by dated roles ("2021 - 2023"), counting overlaps once."""
    current_year = current_year or date.today().year
    spans = []
    for a, b in _RANGE.findall(text):
        end = current_year if not b[:1].isdigit() else int(b)
        if int(a) <= end <= current_year:
            spans.append((int(a), end))
    total, last_end = 0, None
    for a, b in sorted(spans):                       # union of overlapping jobs
        if last_end is None or a >= last_end:
            total += b - a
            last_end = b
        elif b > last_end:
            total += b - last_end
            last_end = b
    return total, len(spans)


def parse_resume(text, name="resume"):
    sections = split_sections(text)
    exp_text = "\n".join(line for h, ls in sections if re.search(r"experience|employment|work|career", h) for line in ls)
    edu_text = "\n".join(line for h, ls in sections if re.search(r"education|academic|qualification", h) for line in ls)
    skill_lines = [line for h, ls in sections if re.search(r"skill|tool|competenc|technolog", h) for line in ls]

    skills = find_skills(text)
    # anything listed under 'Skills' that the taxonomy does not know = unrecognised (possible emerging skill)
    unknown = []
    for line in skill_lines:
        for item in re.split(r"[,;|•·/]|\s-\s|\band\b", line):
            item = item.strip(" .:-*()").strip()
            if 2 <= len(item) <= 40 and len(item.split()) <= 4 and not find_skills(item) and not item.isdigit():
                unknown.append(item)

    stated = [int(n) for n in _YEARS_STATED.findall(text)]
    ranged, n_ranges = years_from_ranges(exp_text or text.replace(edu_text, ""))
    if stated:
        years, years_src = max(stated), "stated in resume"
    elif n_ranges:
        years, years_src = ranged, f"from {n_ranges} dated role(s)"
    else:
        years, years_src = 0, "not found (assumed 0)"

    edu = find_education(edu_text or text, "max")
    top_text = "\n".join(sections[0][1][:6]) if sections else text[:300]
    state = find_state(top_text) or find_state(text)
    first = next((line.strip() for line in text.splitlines() if line.strip()), name)
    return {"name": first[:60], "skills": sorted(skills), "evidence": skills, "unknown_skills": sorted(set(unknown)),
            "years_experience": int(years), "years_source": years_src,
            "education": edu or "secondary", "education_found": bool(edu),
            "state": state or "Unknown", "state_found": bool(state)}


def parse_job(text):
    sections = split_sections(text)
    core, optional, other = {}, {}, {}
    for header, lines in sections:
        h = header.lower()
        bucket = (optional if re.search(r"nice|prefer|desirabl|advantage|bonus|plus", h)
                  else core if re.search(r"require|qualif|must|essential|need|skill|who you are|competenc", h)
                  else other)
        for line in lines:
            if find_education(line):                # 'Degree in Statistics' is a qualification, not a skill
                continue
            line_bucket = optional if re.search(r"nice to have|preferred|is a plus|an advantage|desirable|bonus", line, re.I) else bucket
            for s, p in find_skills(line).items():
                line_bucket.setdefault(s, p)
    if not core:                                    # no clear 'Requirements' section: treat everything as core
        core, other = {**other, **core}, {}
    optional = {s: p for s, p in {**other, **optional}.items() if s not in core}

    m = re.search(r"^[ \t]*(?:job title|position|role)[ \t]*[:\-][ \t]*(.+)", text, re.I | re.M)
    title = (m.group(1) if m else next(line for line in text.splitlines() if line.strip())).strip()[:80]
    req_text = "\n".join(
        line for h, ls in sections if re.search(r"require|qualif|must|essential|need|who you are", h) for line in ls
    ) or text
    yrs = re.search(r"(\d{1,2})\s*\+?\s*(?:-|–|to)?\s*(?:\d{1,2})?\s*\+?\s*(?:years?|yrs?)", req_text, re.I)
    edu = find_education(req_text, "min") or find_education(text, "min")
    remote = re.search(r"\bremote\b", text, re.I) and not re.search(r"not remote|no remote", text, re.I)
    loc_line = (
        "\n".join(line for h, ls in sections for line in ls if "location" in h)
        + "\n"
        + "\n".join(line for line in text.splitlines() if re.search(r"location|based in", line, re.I))
    )
    state = find_state(loc_line) or find_state(text)
    return {"title": title, "core_skills": sorted(core), "optional_skills": sorted(optional),
            "evidence": {**optional, **core},
            "min_experience": int(yrs.group(1)) if yrs else 0, "experience_found": bool(yrs),
            "min_education": edu or "secondary", "education_found": bool(edu),
            "state": "Remote" if remote and not state else (state or "Remote"), "state_found": bool(state or remote),
            "remote_ok": bool(remote)}
