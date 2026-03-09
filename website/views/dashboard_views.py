from flask import Blueprint, render_template
from website import db
from ..models import User, Visit, Action
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    # 1. Top Card Metrics
    total_users = User.query.count()
    users_who_activated = db.session.query(func.count(Action.user_id.distinct())).filter_by(atype='survey_submit').scalar()
    total_visits = Visit.query.count()
    
    activation_rate = round((users_who_activated / total_users * 100), 2) if total_users > 0 else 0

    # 2. Time-Series Logic (Defined outside the loop)
    def get_rate_for_date(d):
        u_count = User.query.filter(func.date(User.created_at) <= d).count()
        a_count = db.session.query(func.count(Action.user_id.distinct())).filter(
            func.date(Action.timestamp) == d, 
            Action.atype == 'survey_submit'
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

    # 3. Optimized Page Stats (One query per page instead of one per visit)
    tracked_pages = ['homepage.html', 'cs', 'econ']
    page_stats = []

    for page_name in tracked_pages:
        # Get counts in bulk
        total_p_visits = Visit.query.filter_by(page=page_name).count()
        unique_p_users = db.session.query(func.count(Visit.user_id.distinct())).filter(Visit.page == page_name).scalar()
        
        # Bounce Calculation: 
        # Count visits where NO action exists for that user within 30 mins of visit timestamp
        bounces = db.session.query(Visit).filter(
            Visit.page == page_name,
            ~Action.query.filter(
                Action.user_id == Visit.user_id,
                Action.timestamp >= Visit.timestamp,
                Action.timestamp <= Visit.timestamp + timedelta(minutes=30)
            ).exists()
        ).count()

        bounce_rate = round((bounces / total_p_visits * 100), 1) if total_p_visits > 0 else 0

        page_stats.append({
            'name': page_name,
            'visitors': total_p_visits,
            'unique': unique_p_users,
            'bounce_rate': bounce_rate
        })

    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        total_visits=total_visits,
        core_actions=users_who_activated,
        activation_rate=activation_rate,
        chart_labels=labels,
        week_0_data=week_0_data,
        week_1_data=week_1_data,
        week_2_data=week_2_data,
        page_stats=sorted(page_stats, key=lambda x: x['visitors'], reverse=True)
    )