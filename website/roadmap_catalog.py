"""Loads roadmap_data_new.json once and provides helpers to slice the catalog."""

import json
import os

from website.onboarding_config import YEAR_KEYS

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "static", "data", "roadmap_data_new.json"
)

with open(_DATA_PATH, encoding="utf-8") as _f:
    CATALOG = json.load(_f)

SECTIONS = CATALOG["schema"]["sections"]


def normalize_year(raw: str) -> str:
    """Map user-facing year strings to JSON block keys, falling back to 'default'."""
    if not raw:
        return "default"
    key = raw.strip().lower()
    return key if key in YEAR_KEYS else "default"


def get_year_block(major: str, year_key: str) -> dict:
    return CATALOG.get(major, {}).get(year_key, CATALOG.get(major, {}).get("default", {}))


def filter_by_goal(block: dict, career_goal: str) -> dict:
    """Return a copy of *block* keeping only items that match *career_goal*.

    Items without a ``goals`` field are treated as universal and always pass.
    The ``exploring`` goal (or empty string) disables filtering entirely.
    Non-list values (hero, highlight) are passed through unchanged.
    """
    if not career_goal or career_goal == "exploring":
        return block
    out: dict = {}
    for key, val in block.items():
        if not isinstance(val, list):
            out[key] = val
            continue
        out[key] = [
            it for it in val
            if "goals" not in it or career_goal in it["goals"]
        ]
    return out


def id_index(major: str, year_key: str) -> dict[str, dict]:
    """Build {id: full_item} for every item in this year block (unfiltered)."""
    block = get_year_block(major, year_key)
    idx: dict[str, dict] = {}
    for section in SECTIONS:
        for item in block.get(section, []):
            if "id" in item:
                idx[item["id"]] = item
    return idx


def compact_catalog(major: str, year_key: str, career_goal: str = "") -> dict:
    """Goal-filtered catalog with id, text, and description for the LLM."""
    block = get_year_block(major, year_key)
    block = filter_by_goal(block, career_goal)
    out: dict[str, list] = {}
    for section in SECTIONS:
        items = block.get(section, [])
        if items:
            out[section] = [
                {"id": it["id"], "text": it["text"], "desc": it.get("popupText", "")}
                for it in items
            ]
    return out


def fallback_sections(
    major: str,
    year_key: str,
    caps: dict[str, int] | None = None,
    career_goal: str = "",
) -> dict:
    """Deterministic top-N per section, filtered by career goal."""
    caps = caps or {}
    block = get_year_block(major, year_key)
    block = filter_by_goal(block, career_goal)
    out: dict[str, list] = {}
    for section in SECTIONS:
        items = block.get(section, [])
        limit = caps.get(section, len(items))
        out[section] = items[:limit]
    return out
