import random

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from .dashboard_views import build_roadmap_dashboard_context
from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..models.tracking import Action, Feedback, User, db
from ..onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    MAJOR_LABELS,
    QUESTIONS,
    QUESTIONS_SHORT,
)
from ..utils import log_visit

# A/B: which onboarding length the user sees
ONBOARDING_AB_COOKIE = "onboarding_ab"
_ONBOARDING_AB_MAX_AGE = 30 * 24 * 60 * 60


landing_blueprint = Blueprint(LANDING_DEFAULT_NAME, __name__)

_PROFILE_MISSING = "Not set yet"
_PROFILE_SHORT_CAREER = (
    "Complete the full onboarding path to see your career goal and stage here."
)


def _mentor_profile_context(tracker_user):
    """
    Sidebar labels from the tracking User row after onboarding submit.

    Class year and major exist for both A/B variants. Career goal and stage
    are only stored for the full Variant B flow.
    """
    if not tracker_user:
        return {
            "profile_class_year": _PROFILE_MISSING,
            "profile_major": _PROFILE_MISSING,
            "profile_career_path": _PROFILE_MISSING,
        }

    class_year = tracker_user.class_year or _PROFILE_MISSING

    major_raw = tracker_user.major
    if major_raw:
        major_display = MAJOR_LABELS.get(
            major_raw,
            major_raw.replace("_", " ").title(),
        )
    else:
        major_display = _PROFILE_MISSING

    variant = (tracker_user.onboarding_variant or "").lower()
    has_career_fields = bool(
        tracker_user.career_goal or tracker_user.career_stage
    )

    if variant == "full" or has_career_fields:
        parts = []

        if tracker_user.career_goal:
            parts.append(
                CAREER_GOAL_LABELS.get(
                    tracker_user.career_goal,
                    tracker_user.career_goal.replace("_", " ").title(),
                )
            )

        if tracker_user.career_stage:
            parts.append(
                CAREER_STAGE_LABELS.get(
                    tracker_user.career_stage,
                    tracker_user.career_stage.replace("_", " ").title(),
                )
            )

        career_path = " — ".join(parts) if parts else _PROFILE_MISSING
    else:
        career_path = _PROFILE_SHORT_CAREER

    return {
        "profile_class_year": class_year,
        "profile_major": major_display,
        "profile_career_path": career_path,
    }


@landing_blueprint.route(PREFIX)
def homepage():
    new_uuid = log_visit(page="homepage.html")
    response = make_response(render_template(LANDING_DEFAULT_NAME + HTML_EXTENSION))

    if new_uuid:
        response.set_cookie("tracking_id", new_uuid, max_age=30 * 24 * 60 * 60)

    return response


@landing_blueprint.route("/track-action", methods=["POST"])
def track_action():
    """Logs non-form actions such as clicks, roadmap metrics, and time-on-page."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    atype = data.get("atype")
    if not atype or not isinstance(atype, str):
        return jsonify({"status": "error", "message": "atype required"}), 400

    atype = atype.strip()[:200]

    detail = data.get("detail")
    if detail is not None and not isinstance(detail, (dict, list)):
        return jsonify({"status": "error", "message": "detail must be an object or array"}), 400

    user_uuid = request.cookies.get("tracking_id")

    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            new_action = Action(atype=atype, user_id=user.id, detail=detail)
            db.session.add(new_action)
            db.session.commit()

    return jsonify({"status": "success"}), 200


def _render_onboarding(*, questions, variant: str, ob_intro_sub: str):
    return render_template(
        "onboarding.html",
        questions=questions,
        onboarding_variant=variant,
        ob_intro_sub=ob_intro_sub,
    )


@landing_blueprint.route("/onboarding")
def onboarding():
    assigned = request.cookies.get(ONBOARDING_AB_COOKIE)

    if assigned not in ("variantA", "variantB"):
        assigned = random.choice(["variantA", "variantB"])
        target = (
            "homepage.onboarding_variant_a"
            if assigned == "variantA"
            else "homepage.onboarding_variant_b"
        )

        response = make_response(redirect(url_for(target)))
        response.set_cookie(
            ONBOARDING_AB_COOKIE,
            assigned,
            max_age=_ONBOARDING_AB_MAX_AGE,
        )
        return response

    if assigned == "variantA":
        return redirect(url_for("homepage.onboarding_variant_a"))

    return redirect(url_for("homepage.onboarding_variant_b"))


@landing_blueprint.route("/onboarding/variantA")
def onboarding_variant_a():
    log_visit(page="onboarding_variant_a.html")
    return _render_onboarding(
        questions=QUESTIONS_SHORT,
        variant="short",
        ob_intro_sub="Two quick questions to get your roadmap.",
    )


@landing_blueprint.route("/onboarding/variantB")
def onboarding_variant_b():
    log_visit(page="onboarding_variant_b.html")
    return _render_onboarding(
        questions=QUESTIONS,
        variant="full",
        ob_intro_sub="Five quick questions to personalise your path.",
    )


@landing_blueprint.route("/submit-info", methods=["POST"])
def submit_info():
    class_year = request.form.get("class_year")
    major = request.form.get("major")
    variant = (request.form.get("onboarding_variant") or "full").lower()

    if variant == "short":
        career_goal = None
        career_stage = None
        priority = None
    else:
        career_goal = request.form.get("career_goal")
        career_stage = request.form.get("career_stage")
        priority = request.form.get("priority")

    user_uuid = request.cookies.get("tracking_id")

    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user.class_year = class_year
            user.major = major
            user.career_goal = career_goal
            user.career_stage = career_stage
            user.priority = priority
            user.onboarding_variant = "short" if variant == "short" else "full"

            core_action = Action(atype="roadmap_submit", user_id=user.id)
            db.session.add(core_action)
            db.session.commit()

            params = {"year": class_year}

            if career_goal:
                params["career_goal"] = career_goal
            if career_stage:
                params["career_stage"] = career_stage
            if priority:
                params["priority"] = priority

            if major == "cs":
                return redirect(url_for("roadmap.cs", **params))
            if major == "econ":
                return redirect(url_for("roadmap.econ", **params))

    return redirect(url_for("homepage.homepage"))


@landing_blueprint.route("/feedback")
def feedback_page():
    log_visit(page="feedback.html")
    return render_template("feedback.html")


@landing_blueprint.route("/mentor")
def mentor_page():
    """Serves the AI Mentor chat page."""
    log_visit(page="mentor.html")

    user_uuid = request.cookies.get("tracking_id")
    tracker_user = User.query.filter_by(uuid=user_uuid).first() if user_uuid else None
    profile = _mentor_profile_context(tracker_user)

    return render_template("mentor.html", **profile)


@landing_blueprint.route("/privacy")
def privacy():
    return render_template("privacy.html")


@landing_blueprint.route("/cookies")
def cookie_policy():
    return render_template("cookies.html")


@landing_blueprint.route("/feedback", methods=["POST"])
def submit_feedback():
    content = request.form.get("feedback_content", "").strip()

    if not content:
        flash("Please enter your feedback before submitting.")
        return redirect(url_for("homepage.feedback_page"))

    user_id = None
    user_uuid = request.cookies.get("tracking_id")

    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user_id = user.id

    feedback = Feedback(content=content, user_id=user_id)
    db.session.add(feedback)
    db.session.commit()

    print("Feedback ID:", feedback.id)

    flash("Thank you for your feedback! We really appreciate it.")
    return redirect(url_for("homepage.feedback_page"))


@landing_blueprint.route("/roadmap_dashboard")
def onboarding_tracker():
    return render_template(
        "roadmap_dashboard.html",
        **build_roadmap_dashboard_context(),
    )