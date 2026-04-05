"""Call LLM to select catalog items for a personalized roadmap."""

import json
import logging
import os

from openai import OpenAI

from website.onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    DEFAULT_SECTION_CAP,
    PRIORITY_CAP_MAP,
    PRIORITY_LABELS,
    SECTION_CAPS,
    STAGE_CAP_MAP,
    _question,
)
from website.roadmap_catalog import (
    SECTIONS,
    compact_catalog,
    fallback_sections,
    get_year_block,
    id_index,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dynamic section caps  (derived from config tables)
# ---------------------------------------------------------------------------

def dynamic_caps(career_stage: str, priority: str) -> dict[str, int]:
    """Compute per-section caps influenced by career stage and priority."""
    caps = {s: SECTION_CAPS.get(s, DEFAULT_SECTION_CAP) for s in SECTIONS}
    caps.update(PRIORITY_CAP_MAP.get(priority, {}))
    # Stage overrides take precedence (e.g. has_offer zeroes internships)
    caps.update(STAGE_CAP_MAP.get(career_stage, {}))
    return caps


# ---------------------------------------------------------------------------
# Prompt builders  (assembled dynamically from config)
# ---------------------------------------------------------------------------

def _build_stage_instructions() -> str:
    lines: list[str] = []
    for opt in _question("career_stage")["options"]:
        hint = opt.get("prompt_hint")
        if hint:
            lines.append(f'- "{opt["label"]}": {hint}')
    return "\n".join(lines)


def _build_priority_instructions() -> str:
    lines: list[str] = [
        "- Return MORE items from the section matching the student's priority.",
        "- Return FEWER items from sections less relevant to their priority.",
    ]
    for opt in _question("priority")["options"]:
        hint = opt.get("prompt_hint")
        if hint:
            lines.append(f'- "{opt["label"]}": {hint}')
    return "\n".join(lines)


def _build_system_prompt(caps: dict[str, int]) -> str:
    caps_desc = ", ".join(f"{s}: max {n}" for s, n in caps.items())

    return (
        "You are Blueprint AI. Given a student profile and a pre-filtered catalog,\n"
        "select the most relevant items for their personalized roadmap.\n\n"

        "CAREER GOAL (filtering already applied):\n"
        "- The catalog has been pre-filtered to items matching the student's career\n"
        "  goal. All items you see are relevant candidates.\n"
        '- For "Still Exploring" students, include a diverse mix across career paths.\n\n'

        "CAREER STAGE (affects tone and level):\n"
        f"{_build_stage_instructions()}\n\n"

        "PRIORITY (affects section weighting):\n"
        f"{_build_priority_instructions()}\n\n"

        "OUTPUT FORMAT:\n"
        "1. Return ONLY a JSON object whose keys are section names.\n"
        "2. Each value is an array of item id strings from the catalog.\n"
        "3. Order by relevance (most relevant first).\n"
        f"4. Caps per section: {caps_desc}. Never exceed them.\n"
        "5. You may return fewer items than the cap.\n"
        "6. Empty sections get an empty array.\n"
        "7. Only use ids present in the catalog. Do NOT invent ids.\n"
        "8. Return valid JSON only — no markdown fences, no commentary."
    )


def _build_user_prompt(profile: dict, major: str, year_key: str) -> str:
    career_goal = profile.get("career_goal", "")
    catalog = compact_catalog(major, year_key, career_goal)

    goal = CAREER_GOAL_LABELS.get(career_goal, career_goal)
    stage = CAREER_STAGE_LABELS.get(
        profile.get("career_stage", ""), profile.get("career_stage", ""),
    )
    priority = PRIORITY_LABELS.get(
        profile.get("priority", ""), profile.get("priority", ""),
    )

    return (
        f"Student profile:\n"
        f"- Major: {major.upper()}\n"
        f"- Class year: {year_key}\n"
        f"- Career goal: {goal}\n"
        f"- Career stage: {stage}\n"
        f"- Current priority: {priority}\n\n"
        f"Catalog (JSON):\n{json.dumps(catalog, ensure_ascii=False)}"
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def personalize(profile: dict, major: str, year_key: str) -> dict:
    """Return resolved sections dict. Falls back deterministically on error."""
    career_goal = profile.get("career_goal", "")
    career_stage = profile.get("career_stage", "")
    priority = profile.get("priority", "")
    caps = dynamic_caps(career_stage, priority)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.info("No OPENAI_API_KEY — returning fallback roadmap.")
        return _wrap(
            major, year_key,
            fallback_sections(major, year_key, caps, career_goal),
            source="fallback",
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _build_system_prompt(caps)},
                {"role": "user", "content": _build_user_prompt(profile, major, year_key)},
            ],
        )
        raw = resp.choices[0].message.content
        selected = json.loads(raw)
    except Exception:
        log.exception("OpenAI call failed — returning fallback.")
        return _wrap(
            major, year_key,
            fallback_sections(major, year_key, caps, career_goal),
            source="fallback",
        )

    idx = id_index(major, year_key)
    sections: dict[str, list] = {}
    for section in SECTIONS:
        ids = selected.get(section, [])
        if not isinstance(ids, list):
            ids = []
        resolved = [idx[i] for i in ids if i in idx]
        cap = caps.get(section, DEFAULT_SECTION_CAP)
        sections[section] = resolved[:cap]

    if not any(sections.values()):
        log.warning("LLM returned no valid ids — falling back.")
        return _wrap(
            major, year_key,
            fallback_sections(major, year_key, caps, career_goal),
            source="fallback",
        )

    return _wrap(major, year_key, sections, source="llm")


def _wrap(major: str, year_key: str, sections: dict, *, source: str) -> dict:
    block = get_year_block(major, year_key)
    return {
        "hero": block.get("hero", ""),
        "highlight": block.get("highlight", ""),
        "sections": sections,
        "source": source,
    }
