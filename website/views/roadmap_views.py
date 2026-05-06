import hashlib
import json

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from website.consts import (
    CS_DEFAULT_NAME,
    ECON_DEFAULT_NAME,
    HTML_EXTENSION,
    LANDING_DEFAULT_NAME,
    MAJOR_SPECIFIC_FOLDER_NAME,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
)
from website.onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    MAJOR_LABELS,
    PRIORITY_LABELS,
)
from website.roadmap_catalog import get_year_block, normalize_year
from website.services.roadmap_openai import personalize
from website.utils import log_visit

roadmap_blueprint = Blueprint(ROADMAP_DEFAULT_NAME, __name__)


def _profile_context():
    return {
        "class_year": request.args.get("year", ""),
        "career_goal": CAREER_GOAL_LABELS.get(request.args.get("career_goal", ""), ""),
        "career_stage": CAREER_STAGE_LABELS.get(
            request.args.get("career_stage", ""), ""
        ),
        "priority": PRIORITY_LABELS.get(request.args.get("priority", ""), ""),
    }


def _render_roadmap_shell(major: str):
    year_key = normalize_year(request.args.get("year", ""))
    block = get_year_block(major, year_key)
    major_label = MAJOR_LABELS.get(major, major.upper())
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + major + HTML_EXTENSION,
        **_profile_context(),
        major=major,
        major_label=major_label,
        hero=block.get("hero", ""),
        highlight=block.get("highlight", ""),
    )


@roadmap_blueprint.route(PREFIX)
def roadmap():
    return redirect(url_for(LANDING_DEFAULT_NAME + ".onboarding"))


@roadmap_blueprint.route(CS_DEFAULT_NAME)
def cs():
    log_visit(page="cs")
    return _render_roadmap_shell("cs")


@roadmap_blueprint.route(ECON_DEFAULT_NAME)
def econ():
    log_visit(page="econ")
    return _render_roadmap_shell("econ")


def _cache_key(profile: dict) -> str:
    raw = json.dumps(profile, sort_keys=True)
    return "roadmap_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


@roadmap_blueprint.route("personalize", methods=["POST"])
def personalize_roadmap():
    print("Personalization request received with data:", request.get_json())
    data = request.get_json(silent=True) or {}
    major = data.get("major", "cs").lower()
    if major not in ("cs", "econ"):
        major = "cs"

    profile = None

    year_key = normalize_year(data.get("year", ""))


    if current_user.is_authenticated:
        profile = {
        "major": major,
        "year": year_key,
        "career_goal": data.get("career_goal", ""),
        "career_stage": data.get("career_stage", ""),
        "priority": data.get("priority", ""),
        }
        current_user.major = major
        current_user.year = year_key
        current_user.career_goal = data.get("career_goal", "")
        current_user.career_stage = data.get("career_stage", "")
        current_user.priority = data.get("priority", "")
        current_user.save()
    else:
        profile = {
            "major": major,
            "year": year_key,
            "career_goal": data.get("career_goal", ""),
            "career_stage": data.get("career_stage", ""),
            "priority": data.get("priority", ""),
        }

    ck = _cache_key(profile)
    cached = session.get(ck)
    if cached:
        return jsonify(cached)

    result = personalize(profile, major, year_key)
    session[ck] = result
    return jsonify(result)
