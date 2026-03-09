from flask import Blueprint, render_template
from ..models import User, Visit, Action
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    # Top Card Metrics 
    total_users = User.query.count()
    core_actions_total = Action.query.filter_by(atype='survey_submit').count()
    total_visits = Visit.query.count()
    
    unique_visitors = Visit.query.distinct(Visit.user_id).count()
    activation_rate = 0
    if unique_visitors > 0:
        activation_rate = round((core_actions_total / unique_visitors) * 100, 2)

    # --- 3-Week Time-Series Logic ---
    today = datetime.utcnow().date()
    labels = []
    week_0_data = [] # Current 7 days
    week_1_data = [] # 7-14 days ago
    week_2_data = [] # 14-21 days ago

    # Iterate through the last 7 days (from 6 days ago up to today)
    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        
        # 1. Labels based on the current 7-day window
        labels.append(target_day.strftime('%a %d'))

        # Helper to query data for a specific date
        def get_rate_for_date(d):
            v = Visit.query.filter(func.date(Visit.timestamp) == d).distinct(Visit.user_id).count()
            a = Action.query.filter(func.date(Action.timestamp) == d, Action.atype == 'survey_submit').count()
            return round((a / v * 100), 1) if v > 0 else 0

        # 2. Populate the 3 different lines
        week_0_data.append(get_rate_for_date(target_day))                   # Current week
        week_1_data.append(get_rate_for_date(target_day - timedelta(days=7))) # -1 week
        week_2_data.append(get_rate_for_date(target_day - timedelta(days=14)))# -2 weeks

        tracked_pages = ['homepage.html', 'cs.html', 'econ.html']
        page_stats = []

        for page_name in tracked_pages:
            # 1. Get all visits for this page
            all_visits = Visit.query.filter_by(page=page_name).all()
            total_p_visits = len(all_visits)
            
            # 2. Unique Users
            unique_p_users = Visit.query.filter_by(page=page_name).distinct(Visit.user_id).count()
            
            # 3. Calculate Bounces (Visits with no corresponding Actions)
            bounces = 0
            for visit in all_visits:
                # Check if this user performed ANY action after this specific visit timestamp
                # Limit the search to within 30 minutes of the visit to define a 'session'
                session_end = visit.timestamp + timedelta(minutes=30)
                
                has_action = Action.query.filter(
                    Action.user_id == visit.user_id,
                    Action.timestamp >= visit.timestamp,
                    Action.timestamp <= session_end
                ).first()

                if not has_action:
                    bounces += 1

            # 4. Calculate Final Bounce Rate
            bounce_rate = round((bounces / total_p_visits * 100), 1) if total_p_visits > 0 else 0

            page_stats.append({
                'name': page_name,
                'visitors': total_p_visits,
                'unique': unique_p_users,
                'bounce_rate': bounce_rate
            })

        # Sort by popularity
        page_stats = sorted(page_stats, key=lambda x: x['visitors'], reverse=True)

    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        total_visits=total_visits,
        core_actions=core_actions_total,
        activation_rate=activation_rate,
        chart_labels=labels,
        week_0_data=week_0_data,
        week_1_data=week_1_data,
        week_2_data=week_2_data,
        page_stats=page_stats
    )