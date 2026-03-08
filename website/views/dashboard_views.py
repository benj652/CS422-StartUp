from flask import Blueprint, render_template
from ..consts import DASHBOARD_DEFAULT_NAME, PREFIX, HTML_EXTENSION

dashboard_blueprint = Blueprint(DASHBOARD_DEFAULT_NAME, __name__)

@dashboard_blueprint.route(PREFIX)
def dashboard():
    
    return render_template(DASHBOARD_DEFAULT_NAME + HTML_EXTENSION) 
