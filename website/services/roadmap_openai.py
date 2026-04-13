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


def dynamic_caps(career_stage: str, priority: str) -> dict[str, int]:
    """Compute per-section caps influenced by career stage and priority."""
    caps = {s: SECTION_CAPS.get(s, DEFAULT_SECTION_CAP) for s in SECTIONS}
    caps.update(PRIORITY_CAP_MAP.get(priority, {}))
    caps.update(STAGE_CAP_MAP.get(career_stage, {}))
    return caps


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
        "You are Blueprint AI. Given a student profile and a pre-filtered catalog, "
        "select the most relevant items for their personalized roadmap.\n\n"

        "CAREER GOAL (filtering already applied):\n"
        "- The catalog has already been filtered to items that can fit the student's goal.\n"
        "- Choose the strongest next steps, not generic filler.\n\n"

        "CAREER STAGE (affects tone and level):\n"
        f"{_build_stage_instructions()}\n\n"

        "PRIORITY (affects section weighting):\n"
        f"{_build_priority_instructions()}\n\n"

        "OUTPUT FORMAT:\n"
        "1. Return ONLY valid JSON whose keys are section names.\n"
        "2. Each section value must be an array of objects.\n"
        '3. Each object must contain "id", "summary", and "whyRecommended".\n'
        '4. "id" must be an item id from the catalog.\n'
        '5. "summary" must be a short 6-14 word card preview.\n'
        '6. "whyRecommended" must be 2-3 sentences and must explain:\n'
        "   - why this specific item matters,\n"
        "   - why it is a good next step right now,\n"
        "   - how it connects to the student's stated goal/stage/priority.\n"
        "7. Do NOT reuse the same sentence structure across items.\n"
        "8. Avoid generic phrasing like 'this fits your roadmap because...'\n"
        "9. Mention the actual opportunity/class/resource by name or concrete function.\n"
        "10. Explanations should sound specific to the item, not interchangeable.\n"
        f"11. Caps per section: {caps_desc}. Never exceed them.\n"
        "12. Only use ids present in the catalog. Do NOT invent ids.\n"
        "13. Return valid JSON only — no markdown fences, no commentary."
    )


def _build_user_prompt(profile: dict, major: str, year_key: str) -> str:
    career_goal = profile.get("career_goal", "")
    catalog = compact_catalog(major, year_key, career_goal)

    goal = CAREER_GOAL_LABELS.get(career_goal, career_goal)
    stage = CAREER_STAGE_LABELS.get(
        profile.get("career_stage", ""),
        profile.get("career_stage", ""),
    )
    priority = PRIORITY_LABELS.get(
        profile.get("priority", ""),
        profile.get("priority", ""),
    )

    return (
        f"Student profile:\n"
        f"- Major: {major.upper()}\n"
        f"- Class year: {year_key}\n"
        f"- Career goal: {goal}\n"
        f"- Career stage: {stage}\n"
        f"- Current priority: {priority}\n\n"
        "Write explanations that do not repeat the same wording across items. "
        "For opportunities, explain the strategic value of the program and why it is timely. "
        "For classes, explain what foundation they build and why taking them now matters. "
        "For networking/resources, explain the practical benefit and next-step logic.\n\n"
        f"Catalog (JSON):\n{json.dumps(catalog, ensure_ascii=False)}"
    )


def _default_summary(item: dict) -> str:
    """Return a short visible summary for the roadmap card."""
    popup = (item.get("popupText") or "").strip()
    if popup:
        if len(popup) <= 90:
            return popup

        trimmed = popup[:110]
        last_space = trimmed.rfind(" ")
        if last_space > 60:
            trimmed = trimmed[:last_space]

        return trimmed.rstrip(" ,;:-") + "…"

    text = (item.get("text") or "Recommendation").strip()
    return f"Recommended option: {text}"


def _fallback_why_recommended(item: dict, profile: dict, section: str) -> str:
    """Generate a more specific non-repetitive reason if the LLM does not return one."""
    name = item.get("text", "This recommendation")
    goal = CAREER_GOAL_LABELS.get(profile.get("career_goal", ""), "your goals").lower()
    stage = CAREER_STAGE_LABELS.get(
        profile.get("career_stage", ""), "your current stage"
    ).lower()
    priority = PRIORITY_LABELS.get(
        profile.get("priority", ""), "your current focus"
    ).lower()

    section_writers = {
        "classes": (
            f"{name} is worth prioritizing now because it builds core academic groundwork "
            f"that will support your longer-term path in {goal}. "
            f"At your current stage ({stage}), getting this foundation in place is a smart move "
            f"while your main focus is {priority}."
        ),
        "programs": (
            f"{name} matters because it gives you early exposure to the kinds of roles and employers "
            f"connected to {goal}. For someone at the '{stage}' stage, it is a strong next step because "
            f"it helps you explore real opportunities without waiting until recruiting becomes more urgent."
        ),
        "internships": (
            f"{name} is a useful next step because it gives you hands-on experience that moves you closer "
            f"to {goal}. Given that you are currently {stage}, this is the kind of opportunity that can turn "
            f"general interest into concrete experience."
        ),
        "projects": (
            f"{name} is important because it helps you build proof of skill, not just interest, in {goal}. "
            f"That makes it especially valuable right now while your focus is {priority}."
        ),
        "networking": (
            f"{name} is a strong next step because it helps you learn how people actually enter fields related "
            f"to {goal}. At your current stage ({stage}), that kind of relationship-building is often more useful "
            f"than rushing into overly specific commitments."
        ),
        "resources": (
            f"{name} is useful because it helps you make better decisions about your path toward {goal}. "
            f"Since your current priority is {priority}, this gives you practical guidance you can act on right away."
        ),
        "full_time_roles": (
            f"{name} is relevant because it gives you a clearer view of where this path can lead after college. "
            f"Even at the {stage} stage, understanding that endpoint can help you make smarter choices now."
        ),
    }

    return section_writers.get(
        section,
        f"{name} is a strong next step because it supports your path toward {goal} "
        f"and fits what matters most for you right now: {priority}.",
    )


def _decorate_fallback_sections(sections: dict, profile: dict) -> dict:
    """Add summary and whyRecommended fields to deterministic fallback items."""
    decorated: dict[str, list] = {}

    for section, items in sections.items():
        decorated[section] = []
        for item in items:
            new_item = dict(item)
            new_item["summary"] = _default_summary(new_item)
            new_item["whyRecommended"] = _fallback_why_recommended(
                new_item, profile, section
            )
            decorated[section].append(new_item)

    return decorated


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
            major,
            year_key,
            _decorate_fallback_sections(
                fallback_sections(major, year_key, caps, career_goal),
                profile,
            ),
            source="fallback",
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.5,
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
            major,
            year_key,
            _decorate_fallback_sections(
                fallback_sections(major, year_key, caps, career_goal),
                profile,
            ),
            source="fallback",
        )

    idx = id_index(major, year_key)
    sections: dict[str, list] = {}

    for section in SECTIONS:
        raw_items = selected.get(section, [])
        if not isinstance(raw_items, list):
            raw_items = []

        resolved = []
        for entry in raw_items:
            if not isinstance(entry, dict):
                continue

            item_id = entry.get("id")
            if item_id not in idx:
                continue

            base_item = dict(idx[item_id])
            base_item["summary"] = entry.get("summary") or _default_summary(base_item)
            base_item["whyRecommended"] = (
                entry.get("whyRecommended")
                or _fallback_why_recommended(base_item, profile, section)
            )
            resolved.append(base_item)

        cap = caps.get(section, DEFAULT_SECTION_CAP)
        sections[section] = resolved[:cap]

    if not any(sections.values()):
        log.warning("LLM returned no valid ids — falling back.")
        return _wrap(
            major,
            year_key,
            _decorate_fallback_sections(
                fallback_sections(major, year_key, caps, career_goal),
                profile,
            ),
            source="fallback",
        )

    return _wrap(major, year_key, sections, source="llm")


def _wrap(major: str, year_key: str, sections: dict, *, source: str) -> dict:
    """Return the final roadmap response payload."""
    block = get_year_block(major, year_key)
    return {
        "hero": block.get("hero", ""),
        "highlight": block.get("highlight", ""),
        "sections": sections,
        "source": source,
    }