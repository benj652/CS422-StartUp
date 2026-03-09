from flask import Blueprint, render_template

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from flask import Blueprint, render_template, request, make_response, redirect, url_for
from ..models.tracking import User, db
from ..utils import log_visit
from flask import request, make_response

landing_blueprint = Blueprint(LANDING_DEFAULT_NAME, __name__)


@landing_blueprint.route(PREFIX)
def homepage():
    new_uuid = log_visit(page="homepage.html")
    response = make_response(render_template(LANDING_DEFAULT_NAME + HTML_EXTENSION))
    
    if new_uuid:
        # Set cookie to expire in 30 days
        response.set_cookie('tracking_id', new_uuid, max_age=30*24*60*60)
    
    return response


@landing_blueprint.route('/submit-info', methods=['POST'])
def submit_info():
    # Get the data from the form
    class_year = request.form.get('class_year')
    major = request.form.get('major')
    
    # Find the current user via cookie
    user_uuid = request.cookies.get('tracking_id')
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            # 3. Update their info in the DB
            user.class_year = class_year
            user.major = major
            db.session.commit()
            
    # 4. Routing Logic: Redirect based on major
    if major == 'cs':
        return redirect(url_for('roadmap.cs'))
    elif major == 'econ':
        return redirect(url_for('roadmap.econ'))
    
    return redirect(url_for('landing.homepage'))