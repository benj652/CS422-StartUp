from flask import Blueprint, render_template
from ..models import User, Visit, Action
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION
from sqlalchemy import func

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    # 1. Total Users 
    total_users = User.query.count()

    # 2. Total New Users (Users joined in the last 24 hours)
    # new_users = User.query.filter(User.major.isnot(None)).count()

    # 3. Core Action Completions (Total Submits)
    core_actions = Action.query.filter_by(atype='survey_submit').count()

    # 4. Activation Rate (Percentage of visitors who submitted)
    total_visits = Visit.query.distinct(Visit.user_id).count()
    activation_rate = 0
    if total_visits > 0:
        activation_rate = round((core_actions / total_visits) * 100, 2)

    return render_template(
        DASHBOARD_DEFAULT_NAME + HTML_EXTENSION,
        total_users=total_users,
        new_users=50,
        core_actions=core_actions,
        activation_rate=activation_rate
    )