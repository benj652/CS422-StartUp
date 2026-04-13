"""Single source of truth for every onboarding option."""

from __future__ import annotations

DEFAULT_SECTION_CAP = 6

SECTION_CAPS: dict[str, int] = {
    "classes": 6,
    "programs": 6,
    "internships": 6,
    "full_time_roles": 4,
    "projects": 8,
    "networking": 4,
    "resources": 6,
}

# ── Onboarding questions ───────────────────────────────────────────────

QUESTIONS: list[dict] = [
    {
        "name": "class_year",
        "title": "What year are you?",
        "layout": "4col",
        "options": [
            {"key": "Freshman",  "label": "Freshman",  "subtitle": "1st year"},
            {"key": "Sophomore", "label": "Sophomore", "subtitle": "2nd year"},
            {"key": "Junior",    "label": "Junior",    "subtitle": "3rd year"},
            {"key": "Senior",    "label": "Senior",    "subtitle": "4th year"},
        ],
    },
    {
        "name": "major",
        "title": "What's your major?",
        "layout": "2col",
        "options": [
            {"key": "cs",   "label": "Computer Science"},
            {"key": "econ", "label": "Economics"},
        ],
    },
    {
        "name": "career_goal",
        "title": "What's your career goal?",
        "layout": "3col",
        "options": [
            {"key": "software_engineer", "label": "Software Engineer"},
            {"key": "data_science",      "label": "Data Scientist / Analyst"},
            {"key": "product_manager",   "label": "Product Manager"},
            {"key": "finance",           "label": "Finance / Banking"},
            {"key": "consulting",        "label": "Consulting"},
            {"key": "exploring",         "label": "Still Exploring"},
        ],
    },
    {
        "name": "career_stage",
        "title": "Where are you in your career journey?",
        "layout": "2col",
        "options": [
            {
                "key": "no_internships",
                "label": "No internships yet",
                "subtitle": "Just getting started",
                "prompt_hint": (
                    "Favor introductory programs, beginner-friendly projects, "
                    "and foundational learning resources. Include some "
                    "internships but emphasize preparation over competitive "
                    "listings."
                ),
                "cap_adjustments": {"internships": 3, "programs": 6},
            },
            {
                "key": "applying",
                "label": "Currently applying",
                "subtitle": "In the recruiting process",
                "prompt_hint": (
                    "Maximize internship and program listings. Include "
                    "interview prep and practical skill-building projects."
                ),
            },
            {
                "key": "has_internship",
                "label": "Had 1+ internship",
                "subtitle": "Building experience",
                "prompt_hint": (
                    "Favor advanced projects, competitive programs, and items "
                    "that build on existing experience. Include full-time "
                    "roles where available."
                ),
            },
            {
                "key": "has_offer",
                "label": "Have a full-time offer",
                "subtitle": "Finishing strong",
                "prompt_hint": (
                    "Do NOT include internship listings. Focus on advanced "
                    "projects, capstone work, and continued growth resources."
                ),
                "cap_adjustments": {"internships": 0, "full_time_roles": 6},
            },
        ],
    },
    {
        "name": "priority",
        "title": "What matters most to you right now?",
        "layout": "2col",
        "options": [
            {
                "key": "classes",
                "label": "Finding the right classes",
                "subtitle": "Build the best academic path",
                "prompt_hint": "Maximize the classes section.",
                "cap_adjustments": {"classes": 6, "projects": 4, "internships": 3},
            },
            {
                "key": "internship",
                "label": "Landing an internship",
                "subtitle": "Break into the industry",
                "prompt_hint": "Maximize internships and programs sections.",
                "cap_adjustments": {"internships": 6, "programs": 6, "projects": 4},
            },
            {
                "key": "projects",
                "label": "Building projects",
                "subtitle": "Grow my portfolio",
                "prompt_hint": "Maximize the projects section.",
                "cap_adjustments": {"projects": 8, "internships": 3},
            },
            {
                "key": "networking",
                "label": "Networking & recruiting",
                "subtitle": "Expand my connections",
                "prompt_hint": "Maximize networking and programs sections.",
                "cap_adjustments": {"networking": 4, "programs": 6, "projects": 4},
            },
        ],
    },
]

QUESTIONS_SHORT: list[dict] = QUESTIONS[:2]

def _question(name: str) -> dict:
    """Return the question dict whose ``name`` matches."""
    for q in QUESTIONS:
        if q["name"] == name:
            return q
    raise KeyError(f"Unknown question: {name!r}")


def labels(name: str) -> dict[str, str]:
    """Build {key: label} for a given question name."""
    return {o["key"]: o["label"] for o in _question(name)["options"]}


def _cap_map(name: str) -> dict[str, dict[str, int]]:
    """Build {option_key: cap_adjustments} for options that define them."""
    return {
        o["key"]: o["cap_adjustments"]
        for o in _question(name)["options"]
        if "cap_adjustments" in o
    }


CAREER_GOAL_LABELS:  dict[str, str] = labels("career_goal")
CAREER_STAGE_LABELS: dict[str, str] = labels("career_stage")
PRIORITY_LABELS:     dict[str, str] = labels("priority")
MAJOR_LABELS:        dict[str, str] = labels("major")

STAGE_CAP_MAP:    dict[str, dict[str, int]] = _cap_map("career_stage")
PRIORITY_CAP_MAP: dict[str, dict[str, int]] = _cap_map("priority")

YEAR_KEYS: list[str] = [o["key"].lower() for o in _question("class_year")["options"]]
