from flask import Blueprint, render_template
from ..models import User, Visit, Action
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    #Top Card Metrics
    total_users = User.query.count()
    core_actions_total = Action.query.filter_by(atype='survey_submit').count()
    total_landing_visits = Visit.query.filter(Visit.page.ilike('%landing.html%')).count()
    
    # Overall Activation Rate
    unique_visitors = Visit.query.distinct(Visit.user_id).count()
    activation_rate = 0
    if unique_visitors > 0:
        activation_rate = round((core_actions_total / unique_visitors) * 100, 2)

    # --- Time-Series Chart Logic ---
    today = datetime.utcnow().date()
    
    def get_daily_rates(days_back):
        rates = []
        labels = []
        for i in range(days_back, -1, -1):
            target_date = today - timedelta(days=i)
            
            # Count unique visitors on this day
            daily_visits = Visit.query.filter(func.date(Visit.timestamp) == target_date).distinct(Visit.user_id).count()
            # Count submits on this day
            daily_actions = Action.query.filter(func.date(Action.timestamp) == target_date, Action.atype == 'survey_submit').count()
            
            rate = round((daily_actions / daily_visits * 100), 1) if daily_visits > 0 else 0
            rates.append(rate)
            labels.append(target_date.strftime('%b %d')) 
        return rates, labels

    three_weeks_data, three_weeks_labels = get_daily_rates(21)
    one_week_data, one_week_labels = get_daily_rates(7)

    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        total_landing_visits=total_landing_visits,
        core_actions=core_actions_total,
        activation_rate=activation_rate,
        three_weeks_data=three_weeks_data,
        three_weeks_labels=three_weeks_labels,
        one_week_data=one_week_data,
        one_week_labels=one_week_labels
    )