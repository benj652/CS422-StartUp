import csv
from datetime import datetime, timedelta
from io import StringIO

from flask import Blueprint, Response, render_template
from sqlalchemy import func
from sqlalchemy.orm import aliased

from website import db
from ..consts import DASHBOARD_DEFAULT_NAME, HTML_EXTENSION, PREFIX
from ..models import Action, Feedback, User, Visit
from ..onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    MAJOR_LABELS,
    PRIORITY_LABELS,
)

VARIANT_ROWS = (
    ("Variant A (short onboarding)", "short"),
    ("Variant B (full onboarding)", "full"),
)


def _safe_int(value):
    return int(value or 0)


def _safe_percent(numerator, denominator, places=1):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, places)


def _action_user_count(atype):
    return _safe_int(
        db.session.query(func.count(func.distinct(Action.user_id)))
        .filter(Action.atype == atype, Action.user_id.isnot(None))
        .scalar()
    )


def _active_user_count():
    """
    Count users who have actually appeared in tracking data.

    This avoids inflated dashboard numbers from empty User rows while still
    counting anonymous users who only visited pages and never submitted onboarding.
    """
    visit_ids = {
        row[0]
        for row in db.session.query(Visit.user_id)
        .filter(Visit.user_id.isnot(None))
        .distinct()
        .all()
    }

    action_ids = {
        row[0]
        for row in db.session.query(Action.user_id)
        .filter(Action.user_id.isnot(None))
        .distinct()
        .all()
    }

    return len(visit_ids | action_ids)


def _count_roadmap_actions(onboarding_variant: str, atype: str) -> int:
    n = (
        db.session.query(func.count(Action.id))
        .join(User, Action.user_id == User.id)
        .filter(
            User.onboarding_variant == onboarding_variant,
            Action.atype == atype,
        )
        .scalar()
    )
    return _safe_int(n)


def _sum_roadmap_time_seconds(onboarding_variant: str) -> int:
    rows = (
        db.session.query(Action)
        .join(User, Action.user_id == User.id)
        .filter(
            User.onboarding_variant == onboarding_variant,
            Action.atype == "roadmap_time_on_page",
        )
        .all()
    )

    total = 0
    for action in rows:
        detail = action.detail
        if not isinstance(detail, dict):
            continue

        sec = detail.get("seconds")
        if sec is None:
            continue

        try:
            total += int(sec)
        except (TypeError, ValueError):
            continue

    return total


def _count_variant_users(onboarding_variant: str) -> int:
    n = (
        db.session.query(func.count(func.distinct(User.id)))
        .filter(User.onboarding_variant == onboarding_variant)
        .scalar()
    )
    return _safe_int(n)


def _count_variant_roadmap_users(onboarding_variant: str) -> int:
    n = (
        db.session.query(func.count(func.distinct(Action.user_id)))
        .join(User, Action.user_id == User.id)
        .filter(
            User.onboarding_variant == onboarding_variant,
            Action.atype == "roadmap_submit",
            Action.user_id.isnot(None),
        )
        .scalar()
    )
    return _safe_int(n)


def _avg_actions_per_user(onboarding_variant: str) -> float:
    users = _count_variant_users(onboarding_variant)
    if not users:
        return 0

    actions = (
        db.session.query(func.count(Action.id))
        .join(User, Action.user_id == User.id)
        .filter(User.onboarding_variant == onboarding_variant)
        .scalar()
    )

    return round(_safe_int(actions) / users, 2)


def _label_for_value(label_map, raw_value):
    if raw_value is None or raw_value == "":
        return "Not answered"
    return label_map.get(raw_value, raw_value)


def _group_user_field(field_name, label_map=None):
    field = getattr(User, field_name)

    rows = (
        db.session.query(field, func.count(User.id))
        .filter(field.isnot(None))
        .group_by(field)
        .order_by(func.count(User.id).desc())
        .all()
    )

    labels = []
    values = []

    for raw_label, count in rows:
        labels.append(_label_for_value(label_map or {}, raw_label))
        values.append(_safe_int(count))

    return labels, values


def _activation_rate_by_day(days=7, offset_days=0):
    today = datetime.utcnow().date()
    labels = []
    values = []

    for i in range(days - 1, -1, -1):
        target_day = today - timedelta(days=i + offset_days)
        labels.append(target_day.strftime("%a %d"))

        users_so_far = (
            db.session.query(func.count(func.distinct(User.id)))
            .filter(func.date(User.created_at) <= target_day)
            .scalar()
        )

        activated_that_day = (
            db.session.query(func.count(func.distinct(Action.user_id)))
            .filter(
                func.date(Action.timestamp) == target_day,
                Action.atype == "get_started_click",
                Action.user_id.isnot(None),
            )
            .scalar()
        )

        values.append(
            _safe_percent(
                _safe_int(activated_that_day),
                _safe_int(users_so_far),
                1,
            )
        )

    return labels, values


def _roadmap_submits_by_day(days=7):
    today = datetime.utcnow().date()
    labels = []
    values = []

    for i in range(days - 1, -1, -1):
        target_day = today - timedelta(days=i)
        labels.append(target_day.strftime("%a %d"))

        count = (
            db.session.query(func.count(Action.id))
            .filter(
                func.date(Action.timestamp) == target_day,
                Action.atype == "roadmap_submit",
            )
            .scalar()
        )
        values.append(_safe_int(count))

    return labels, values


def _build_page_stats():
    tracked_pages = [
        ("homepage.html", "Home"),
        ("onboarding_variant_a.html", "Onboarding Variant A"),
        ("onboarding_variant_b.html", "Onboarding Variant B"),
        ("cs", "Computer Science Roadmap"),
        ("econ", "Economics Roadmap"),
        ("feedback.html", "Feedback"),
    ]

    page_stats = []

    for page_name, display_name in tracked_pages:
        total_p_visits = Visit.query.filter_by(page=page_name).count()

        unique_p_users = _safe_int(
            db.session.query(func.count(func.distinct(Visit.user_id)))
            .filter(Visit.page == page_name, Visit.user_id.isnot(None))
            .scalar()
        )

        bounces = 0
        all_visits_to_page = Visit.query.filter_by(page=page_name).all()

        for visit in all_visits_to_page:
            if visit.user_id is None:
                continue

            three_mins_later = visit.timestamp + timedelta(minutes=3)

            later_visit_exists = db.session.query(
                Visit.query.filter(
                    Visit.user_id == visit.user_id,
                    Visit.id != visit.id,
                    Visit.timestamp > visit.timestamp,
                    Visit.timestamp <= three_mins_later,
                ).exists()
            ).scalar()

            later_action_exists = db.session.query(
                Action.query.filter(
                    Action.user_id == visit.user_id,
                    Action.timestamp > visit.timestamp,
                    Action.timestamp <= three_mins_later,
                ).exists()
            ).scalar()

            if not later_visit_exists and not later_action_exists:
                bounces += 1

        bounce_rate = _safe_percent(bounces, total_p_visits, 1)

        page_stats.append(
            {
                "name": display_name,
                "visitors": total_p_visits,
                "unique": unique_p_users,
                "bounce_rate": bounce_rate,
            }
        )

    return sorted(page_stats, key=lambda x: x["visitors"], reverse=True)


def build_roadmap_dashboard_context():
    """Shared context for the A/B roadmap experiment dashboard."""
    variant_labels = [label for label, _key in VARIANT_ROWS]
    variant_user_counts = []
    variant_submit_rates = []
    variant_click_counts = []
    variant_checkbox_counts = []
    variant_time_minutes = []
    variant_avg_actions = []
    variant_rows = []

    for label, key in VARIANT_ROWS:
        users = _count_variant_users(key)
        roadmap_users = _count_variant_roadmap_users(key)
        clicks = _count_roadmap_actions(key, "roadmap_link_click")
        checkboxes = _count_roadmap_actions(key, "roadmap_checkbox")
        seconds = _sum_roadmap_time_seconds(key)
        minutes = round(seconds / 60, 1)
        submit_rate = _safe_percent(roadmap_users, users, 1)
        avg_actions = _avg_actions_per_user(key)

        variant_user_counts.append(users)
        variant_submit_rates.append(submit_rate)
        variant_click_counts.append(clicks)
        variant_checkbox_counts.append(checkboxes)
        variant_time_minutes.append(minutes)
        variant_avg_actions.append(avg_actions)

        variant_rows.append(
            {
                "label": label,
                "users": users,
                "roadmap_users": roadmap_users,
                "submit_rate": submit_rate,
                "clicks": clicks,
                "checkboxes": checkboxes,
                "time_minutes": minutes,
                "avg_actions": avg_actions,
            }
        )

    best_variant = "Not enough data yet"
    if variant_submit_rates[0] > variant_submit_rates[1]:
        best_variant = "Variant A"
    elif variant_submit_rates[1] > variant_submit_rates[0]:
        best_variant = "Variant B"

    class_year_labels, class_year_values = _group_user_field("class_year")
    major_labels, major_values = _group_user_field("major", MAJOR_LABELS)
    career_goal_labels, career_goal_values = _group_user_field(
        "career_goal",
        CAREER_GOAL_LABELS,
    )
    career_stage_labels, career_stage_values = _group_user_field(
        "career_stage",
        CAREER_STAGE_LABELS,
    )
    priority_labels, priority_values = _group_user_field(
        "priority",
        PRIORITY_LABELS,
    )

    return {
        "variant_rows": variant_rows,
        "variant_labels": variant_labels,
        "variant_user_counts": variant_user_counts,
        "variant_submit_rates": variant_submit_rates,
        "variant_click_counts": variant_click_counts,
        "variant_checkbox_counts": variant_checkbox_counts,
        "variant_time_minutes": variant_time_minutes,
        "variant_avg_actions": variant_avg_actions,
        "best_variant": best_variant,
        "class_year_labels": class_year_labels,
        "class_year_values": class_year_values,
        "major_labels": major_labels,
        "major_values": major_values,
        "career_goal_labels": career_goal_labels,
        "career_goal_values": career_goal_values,
        "career_stage_labels": career_stage_labels,
        "career_stage_values": career_stage_values,
        "priority_labels": priority_labels,
        "priority_values": priority_values,
    }


dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)


@dashboard_blueprint.route("/export-roadmap-metrics.csv")
def export_roadmap_metrics_csv():
    """CSV: one row per onboarding variant, roadmap interaction counts."""
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "Variant",
            "roadmap_checkbox",
            "roadmap_link_click",
            "roadmap_time_on_page_seconds_total",
        ]
    )

    for label, variant_key in VARIANT_ROWS:
        writer.writerow(
            [
                label,
                _count_roadmap_actions(variant_key, "roadmap_checkbox"),
                _count_roadmap_actions(variant_key, "roadmap_link_click"),
                _sum_roadmap_time_seconds(variant_key),
            ]
        )

    data = buf.getvalue()
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=roadmap_metrics_by_variant.csv",
        },
    )


@dashboard_blueprint.route(PREFIX)
def dashboard():
    # Top card metrics
    total_users = _active_user_count()
    total_visits = Visit.query.count()

    users_who_activated = _action_user_count("get_started_click")
    users_who_complete_core_action = _action_user_count("roadmap_submit")

    engagement_rate = _safe_percent(users_who_activated, total_users, 2)
    core_action_rate = _safe_percent(users_who_complete_core_action, total_users, 2)

    # Activation rate chart
    chart_labels, week_0_data = _activation_rate_by_day(days=7, offset_days=0)
    _labels_last_week, week_1_data = _activation_rate_by_day(days=7, offset_days=7)
    _labels_two_weeks, week_2_data = _activation_rate_by_day(days=7, offset_days=14)

    # Profile breakdown charts
    class_year_labels, class_year_values = _group_user_field("class_year")
    major_labels, major_values = _group_user_field("major", MAJOR_LABELS)
    career_goal_labels, career_goal_values = _group_user_field(
        "career_goal",
        CAREER_GOAL_LABELS,
    )
    priority_labels, priority_values = _group_user_field(
        "priority",
        PRIORITY_LABELS,
    )
    roadmap_labels, roadmap_values = _roadmap_submits_by_day(days=7)

    # 14-day bounded retention: did a user submit roadmap again within 14 days?
    Action1 = aliased(Action)
    Action2 = aliased(Action)

    retained_users_count = (
        db.session.query(func.count(func.distinct(Action1.user_id)))
        .join(Action2, Action1.user_id == Action2.user_id)
        .filter(
            Action1.atype == "roadmap_submit",
            Action2.atype == "roadmap_submit",
            Action2.timestamp > Action1.timestamp,
            Action2.timestamp <= Action1.timestamp + timedelta(days=14),
            Action1.user_id.isnot(None),
        )
        .scalar()
    )

    total_core_users = _action_user_count("roadmap_submit")
    retention_rate = _safe_percent(_safe_int(retained_users_count), total_core_users, 1)

    feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()

    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        total_visits=total_visits,
        retention_rate=retention_rate,
        engagement_rate=engagement_rate,
        activation_rate=core_action_rate,
        chart_labels=chart_labels,
        week_0_data=week_0_data,
        week_1_data=week_1_data,
        week_2_data=week_2_data,
        class_year_labels=class_year_labels,
        class_year_values=class_year_values,
        major_labels=major_labels,
        major_values=major_values,
        career_goal_labels=career_goal_labels,
        career_goal_values=career_goal_values,
        priority_labels=priority_labels,
        priority_values=priority_values,
        roadmap_labels=roadmap_labels,
        roadmap_values=roadmap_values,
        page_stats=_build_page_stats(),
        feedback_list=feedback_list,
    )