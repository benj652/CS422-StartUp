from flask import Blueprint, render_template
from website import db
from ..models import User, Visit, Action, Feedback
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION
from sqlalchemy import func
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    # 1. Top Card Metrics
    total_users = User.query.count()
    users_who_activated = db.session.query(func.count(Action.user_id.distinct())).filter_by(atype='get_started_click').scalar()
    total_visits = Visit.query.count()
    users_who_complete_core_action = db.session.query(func.count(Action.user_id.distinct())).filter_by(atype='roadmap_submit').scalar()
    
    engagement_rate = round((users_who_activated / total_users * 100), 2) if total_users > 0 else 0
    core_action_rate = round((users_who_complete_core_action / total_users * 100), 2) if total_users > 0 else 0

    # 2. Time-Series Logic
    def get_rate_for_date(d):
        u_count = User.query.filter(func.date(User.created_at) <= d).count()
        a_count = db.session.query(func.count(Action.user_id.distinct())).filter(
            func.date(Action.timestamp) == d, 
            Action.atype == 'get_started_click'
        ).scalar()
        return round((a_count / u_count * 100), 1) if u_count > 0 else 0

    today = datetime.utcnow().date()
    labels, week_0_data, week_1_data, week_2_data = [], [], [], []

    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        labels.append(target_day.strftime('%a %d'))
        week_0_data.append(get_rate_for_date(target_day))
        week_1_data.append(get_rate_for_date(target_day - timedelta(days=7)))
        week_2_data.append(get_rate_for_date(target_day - timedelta(days=14)))

    # Class Year Data for Bar Chart
    # We query the counts for each year stored in the User model
    year_counts = {
        'Freshman': User.query.filter_by(class_year='Freshman').count(),
        'Sophomore': User.query.filter_by(class_year='Sophomore').count(),
        'Junior': User.query.filter_by(class_year='Junior').count(),
        'Senior': User.query.filter_by(class_year='Senior').count(),
    }
    
    # Format data for the chart (labels and data list)
    class_year_labels = list(year_counts.keys())
    class_year_values = list(year_counts.values())

    # --- 14-Day Bounded Retention (Core Action: roadmap_submit) ---

    # Create an alias of the Action table so we can join it to itself
    Action1 = aliased(Action)
    Action2 = aliased(Action)

    # This query finds unique users (Action1) who have a SECOND action (Action2) 
    # that happened between 1 second and 14 days AFTER the first one.
    retained_users_count = db.session.query(func.count(Action1.user_id.distinct())).join(
        Action2, Action1.user_id == Action2.user_id
    ).filter(
        Action1.atype == 'roadmap_submit',
        Action2.atype == 'roadmap_submit',
        Action2.timestamp > Action1.timestamp,
        Action2.timestamp <= Action1.timestamp + timedelta(days=14)
    ).scalar()

    # Calculate rate against total users who have ever done the core action
    total_core_users = db.session.query(func.count(Action.user_id.distinct())).filter_by(atype='roadmap_submit').scalar()

    retention_rate = round((retained_users_count / total_core_users * 100), 1) if total_core_users > 0 else 0

    # 3. Optimized Page Stats
    tracked_pages = [
        ('homepage.html', 'Home'),
        ('onboarding_variant_a.html', 'Onboarding (variant A)'),
        ('onboarding_variant_b.html', 'Onboarding (variant B)'),
        ('cs', 'CS'),
        ('econ', 'Economics'),
        ('feedback.html', 'Feedback'),
    ]
    page_stats = []

    for page_name, display_name in tracked_pages:
        # 1. Get basic counts
        total_p_visits = Visit.query.filter_by(page=page_name).count()
        unique_p_users = db.session.query(func.count(Visit.user_id.distinct())).filter(Visit.page == page_name).scalar()
        
        # 2. Calculate Bounces
        bounces = 0
        all_visits_to_page = Visit.query.filter_by(page=page_name).all()
        
        for v in all_visits_to_page:
            three_mins_later = v.timestamp + timedelta(minutes=3)
            
            has_further_activity = db.session.query(
                db.session.query(Visit).filter(
                    Visit.user_id == v.user_id,
                    Visit.timestamp > v.timestamp,
                    Visit.timestamp <= three_mins_later
                ).exists() | 
                db.session.query(Action).filter(
                    Action.user_id == v.user_id,
                    Action.timestamp > v.timestamp,
                    Action.timestamp <= three_mins_later
                ).exists()
            ).scalar()

            if not has_further_activity:
                bounces += 1

        # 3. Calculate Rate and Append (OUTSIDE the 'v' loop, INSIDE the 'page_name' loop)
        bounce_rate = round((bounces / total_p_visits * 100), 1) if total_p_visits > 0 else 0

        page_stats.append({
            'name': display_name,
            'visitors': total_p_visits,
            'unique': unique_p_users,
            'bounce_rate': bounce_rate
        })

    feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).all() 
    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        total_visits=total_visits,
        retention_rate=retention_rate,
        engagement_rate=engagement_rate,
        activation_rate=core_action_rate,
        chart_labels=labels,
        week_0_data=week_0_data,
        week_1_data=week_1_data,
        week_2_data=week_2_data,
        class_year_labels=class_year_labels,
        class_year_values=class_year_values,
        page_stats=sorted(page_stats, key=lambda x: x['visitors'], reverse=True),
        feedback_list=feedback_list
    )