import hashlib
import hmac
import os
import random
from datetime import datetime, timedelta

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
from sqlalchemy import func

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..models.tracking import Action, Feedback, User, Visit, db
from ..onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    MAJOR_LABELS,
    PRIORITY_LABELS,
    QUESTIONS,
    QUESTIONS_SHORT,
)
from ..utils import count_distinct_users_who_visited_onboarding_variant, log_visit

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
    Sidebar labels from the tracking User row (onboarding submit).

    Class year and major exist for both A/B variants; career goal and stage
    are only stored for the full (variant B) flow.
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
            major_raw, major_raw.replace("_", " ").title()
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
        # Set cookie to expire in 30 days
        response.set_cookie("tracking_id", new_uuid, max_age=30 * 24 * 60 * 60)

    return response


@landing_blueprint.route("/track-action", methods=["POST"])
def track_action():
    """Logs non-form actions (clicks, roadmap metrics, etc.)."""
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
            ONBOARDING_AB_COOKIE, assigned, max_age=_ONBOARDING_AB_MAX_AGE
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

            params: dict = {"year": class_year}
            if career_goal:
                params["career_goal"] = career_goal
            if career_stage:
                params["career_stage"] = career_stage
            if priority:
                params["priority"] = priority
            if major == "cs":
                return redirect(url_for("roadmap.cs", **params))
            elif major == "econ":
                return redirect(url_for("roadmap.econ", **params))

    return redirect(url_for("homepage.homepage"))


@landing_blueprint.route("/feedback")
def feedback_page():
    log_visit(page="feedback.html")
    return render_template("feedback.html")


@landing_blueprint.route("/mentor")
def mentor_page():
    """Serves the AI Mentor chat page (open to all visitors)."""
    log_visit(page="mentor.html")
    user_uuid = request.cookies.get("tracking_id")
    tracker_user = (
        User.query.filter_by(uuid=user_uuid).first() if user_uuid else None
    )
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


def variant_metrics(variant_key: str) -> dict:
    """Return per-variant totals and normalized per-user averages.

    users_count is distinct users who visited that variant's onboarding page
    (Visit), not User.onboarding_variant from form submit. Averages divide by
    that visit-based headcount while action totals still use submitted variant.
    """
    users_count = count_distinct_users_who_visited_onboarding_variant(variant_key)
    checkboxes = int(
        db.session.query(func.count(Action.id))
        .join(User, Action.user_id == User.id)
        .filter(User.onboarding_variant == variant_key, Action.atype == "roadmap_checkbox")
        .scalar() or 0
    )
    clicks = int(
        db.session.query(func.count(Action.id))
        .join(User, Action.user_id == User.id)
        .filter(User.onboarding_variant == variant_key, Action.atype == "roadmap_link_click")
        .scalar() or 0
    )
    status_changes = int(
        db.session.query(func.count(Action.id))
        .join(User, Action.user_id == User.id)
        .filter(
            User.onboarding_variant == variant_key,
            Action.atype == "roadmap_status_change",
        )
        .scalar() or 0
    )
    total_seconds = 0
    for (detail,) in (
        db.session.query(Action.detail)
        .join(User, Action.user_id == User.id)
        .filter(User.onboarding_variant == variant_key, Action.atype == "roadmap_time_on_page")
        .all()
    ):
        if isinstance(detail, dict):
            try:
                total_seconds += int(detail.get("seconds", 0))
            except (TypeError, ValueError):
                pass

    def _avg(value: int) -> float:
        if users_count <= 0:
            return 0.0
        return round(value / users_count, 2)

    return {
        "users": users_count,
        "checkboxes": checkboxes,
        "clicks": clicks,
        "status_changes": status_changes,
        "time_seconds": total_seconds,
        "avg_clicks_per_user": _avg(clicks),
        "avg_checkboxes_per_user": _avg(checkboxes),
        "avg_status_changes_per_user": _avg(status_changes),
        "avg_time_seconds_per_user": _avg(total_seconds),
    }


def _daily_time_seconds(variant_key: str, day) -> int:
    """Sum roadmap_time_on_page seconds for one variant on one date."""
    total = 0
    for (detail,) in (
        db.session.query(Action.detail)
        .join(User, Action.user_id == User.id)
        .filter(
            User.onboarding_variant == variant_key,
            Action.atype == "roadmap_time_on_page",
            func.date(Action.timestamp) == day,
        )
        .all()
    ):
        if isinstance(detail, dict):
            try:
                total += int(detail.get("seconds", 0))
            except (TypeError, ValueError):
                pass
    return total


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
    # Compare digests so lengths can differ and comparison stays constant-time.
    digest = hashlib.sha256
    p_hash = digest(provided.encode("utf-8")).digest()
    e_hash = digest(expected.encode("utf-8")).digest()
    return hmac.compare_digest(p_hash, e_hash)


@landing_blueprint.route("/roadmap_dashboard/login", methods=["POST"])
def roadmap_dashboard_login():
    expected_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    expected_password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    provided_email = (request.form.get("admin_email") or "").strip().lower()
    provided_password = (request.form.get("admin_password") or "")

    if not expected_email or not expected_password:
        flash("ADMIN_EMAIL/ADMIN_PASSWORD are not configured on the server.", "danger")
        return redirect(url_for("homepage.onboarding_tracker"))

    email_ok = provided_email == expected_email
    password_ok = _admin_password_is_valid(
        provided=provided_password, expected=expected_password
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
            daily_a=[],
            daily_b=[],
            chart_labels=[],
            career_goal_labels=[],
            career_goal_values=[],
            priority_labels=[],
            priority_values=[],
            class_year_labels=[],
            class_year_values=[],
            major_labels=[],
            major_values=[],
            variant_a={
                "clicks": 0,
                "checkboxes": 0,
                "status_changes": 0,
                "time_seconds": 0,
            },
            variant_b={
                "clicks": 0,
                "checkboxes": 0,
                "status_changes": 0,
                "time_seconds": 0,
            },
        )

    variant_a = variant_metrics("short")
    variant_b = variant_metrics("full")


    priority_labels, priority_values = [], []
    for key, label in PRIORITY_LABELS.items():
        priority_labels.append(label)
        priority_values.append(User.query.filter_by(priority=key).count())

    career_goal_labels, career_goal_values = [], []
    for key, label in CAREER_GOAL_LABELS.items():
        career_goal_labels.append(label)
        career_goal_values.append(User.query.filter_by(career_goal=key).count())

    class_years = ["Freshman", "Sophomore", "Junior", "Senior"]
    class_year_values = [User.query.filter_by(class_year=y).count() for y in class_years]

    major_labels = ["Computer Science", "Economics"]
    major_values = [
        User.query.filter_by(major="cs").count(),
        User.query.filter_by(major="econ").count(),
    ]

    today = datetime.utcnow().date()
    chart_labels, daily_a, daily_b = [], [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime("%a %d"))
        daily_a.append(_daily_time_seconds("short", day))
        daily_b.append(_daily_time_seconds("full", day))

    return render_template(
        "roadmap_dashboard.html",
        priority_labels=priority_labels,
        priority_values=priority_values,
        career_goal_labels=career_goal_labels,
        career_goal_values=career_goal_values,
        variant_a=variant_a,
        variant_b=variant_b,
        class_year_labels=class_years,
        class_year_values=class_year_values,
        major_labels=major_labels,
        major_values=major_values,
        chart_labels=chart_labels,
        daily_a=daily_a,
        daily_b=daily_b,
        is_dashboard_admin=True,
    )
