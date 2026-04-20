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
    url_for,
)
from flask_login import login_required
from sqlalchemy import func

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..models.tracking import Action, Feedback, User, db
from ..onboarding_config import PRIORITY_LABELS, QUESTIONS, QUESTIONS_SHORT
from ..utils import log_visit

# A/B: which onboarding length the user sees
ONBOARDING_AB_COOKIE = "onboarding_ab"
_ONBOARDING_AB_MAX_AGE = 30 * 24 * 60 * 60


landing_blueprint = Blueprint(LANDING_DEFAULT_NAME, __name__)


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
@login_required
def mentor_page():
    """Serves the AI Mentor chat page (Google sign-in required)."""
    log_visit(page="mentor.html")
    return render_template("mentor.html")


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
    """Return checkbox count, link-click count, and total time for one variant."""
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
    return {
        "checkboxes": checkboxes,
        "clicks": clicks,
        "time_minutes": round(total_seconds / 60, 1),
    }


def _daily_time_minutes(variant_key: str, day) -> float:
    """Sum roadmap_time_on_page seconds for one variant on one date, return minutes."""
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
    return round(total / 60, 1)


@landing_blueprint.route("/roadmap_dashboard")
def onboarding_tracker():
    variant_a = variant_metrics("short")
    variant_b = variant_metrics("full")

    priority_data = [
        {"label": label, "count": User.query.filter_by(priority=key).count()}
        for key, label in PRIORITY_LABELS.items()
    ]

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
        daily_a.append(_daily_time_minutes("short", day))
        daily_b.append(_daily_time_minutes("full", day))

    return render_template(
        "roadmap_dashboard.html",
        priority_data=priority_data,
        variant_a=variant_a,
        variant_b=variant_b,
        class_year_labels=class_years,
        class_year_values=class_year_values,
        major_labels=major_labels,
        major_values=major_values,
        chart_labels=chart_labels,
        daily_a=daily_a,
        daily_b=daily_b,
    )
