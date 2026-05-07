import hashlib
import hmac
import os
import random

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from .dashboard_views import build_roadmap_dashboard_context
from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..models.tracking import Action, Feedback, User, Visit, db
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
_DASHBOARD_ADMIN_SESSION_KEY = "roadmap_dashboard_admin"


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
        return (
            jsonify(
                {"status": "error", "message": "detail must be an object or array"}
            ),
            400,
        )

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
    editing = request.args.get("editing") == "1"

    if (
        not editing
        and current_user.is_authenticated
        and current_user.major
        and current_user.year
    ):
        major = current_user.major.lower()
        params = {
            "year": current_user.year,
            "career_goal": current_user.career_goal,
            "career_stage": current_user.career_stage,
            "priority": current_user.priority,
        }

        if major == "cs":
            return redirect(url_for("roadmap.cs", **params))
        if major == "econ":
            return redirect(url_for("roadmap.econ", **params))

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


@landing_blueprint.route("/roadmap_dashboard/reset-tracking", methods=["POST"])
def reset_roadmap_tracking():
    if not session.get(_DASHBOARD_ADMIN_SESSION_KEY):
        flash("Please log in as dashboard admin first.", "danger")
        return redirect(url_for("homepage.onboarding_tracker"))

    try:
        Action.query.delete(synchronize_session=False)
        Visit.query.delete(synchronize_session=False)
        Feedback.query.delete(synchronize_session=False)
        User.query.delete(synchronize_session=False)
        db.session.commit()
        flash("Tracking data reset successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not reset tracking data. Please try again.", "danger")

    return redirect(url_for("homepage.onboarding_tracker"))


def _admin_password_is_valid(*, provided: str, expected: str) -> bool:
    if not provided or not expected:
        return False

    digest = hashlib.sha256
    p_hash = digest(provided.encode("utf-8")).digest()
    e_hash = digest(expected.encode("utf-8")).digest()

    return hmac.compare_digest(p_hash, e_hash)


@landing_blueprint.route("/roadmap_dashboard/login", methods=["POST"])
def roadmap_dashboard_login():
    expected_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    expected_password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    provided_email = (request.form.get("admin_email") or "").strip().lower()
    provided_password = request.form.get("admin_password") or ""

    if not expected_email or not expected_password:
        flash("ADMIN_EMAIL/ADMIN_PASSWORD are not configured on the server.", "danger")
        return redirect(url_for("homepage.onboarding_tracker"))

    email_ok = provided_email == expected_email
    password_ok = _admin_password_is_valid(
        provided=provided_password,
        expected=expected_password,
    )

    if email_ok and password_ok:
        session[_DASHBOARD_ADMIN_SESSION_KEY] = True
        session.modified = True
        flash("Admin login successful.", "success")
        return redirect(url_for("homepage.onboarding_tracker"))

    flash("Invalid admin email or password.", "danger")
    return redirect(url_for("homepage.onboarding_tracker"))


@landing_blueprint.route("/roadmap_dashboard/logout", methods=["POST"])
def roadmap_dashboard_logout():
    session.pop(_DASHBOARD_ADMIN_SESSION_KEY, None)
    flash("Logged out of dashboard admin.", "success")
    return redirect(url_for("homepage.onboarding_tracker"))


@landing_blueprint.route("/roadmap_dashboard")
def onboarding_tracker():
    is_dashboard_admin = bool(session.get(_DASHBOARD_ADMIN_SESSION_KEY))

    if not is_dashboard_admin:
        return render_template(
            "roadmap_dashboard.html",
            is_dashboard_admin=False,
        )

    return render_template(
        "roadmap_dashboard.html",
        is_dashboard_admin=True,
        **build_roadmap_dashboard_context(),
    )