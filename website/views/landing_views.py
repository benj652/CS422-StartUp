from flask import Blueprint, flash, jsonify, render_template

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from flask import Blueprint, render_template, request, make_response, redirect, url_for
from ..models.tracking import User, Action, Feedback, db
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

@landing_blueprint.route('/track-action', methods=['POST'])
def track_action():
    """Logs non-form actions like button clicks."""
    data = request.get_json()
    user_uuid = request.cookies.get('tracking_id')
    
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            new_action = Action(atype=data['atype'], user_id=user.id)
            db.session.add(new_action)
            db.session.commit()
    return jsonify({"status": "success"}), 200

@landing_blueprint.route('/submit-info', methods=['POST'])
def submit_info():
    class_year = request.form.get('class_year')
    major = request.form.get('major')
    user_uuid = request.cookies.get('tracking_id')
    
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            # 1. Update user profile
            user.class_year = class_year
            user.major = major
            
            # 2. Log the CORE ACTION (survey_submit)
            core_action = Action(atype='survey_submit', user_id=user.id)
            db.session.add(core_action)
            
            db.session.commit()
            
            # 3. Redirect based on major
            if major == 'cs':
                return redirect(url_for('roadmap.cs', year=class_year))
            elif major == 'econ':
                return redirect(url_for('roadmap.econ', year=class_year))
                
    return redirect(url_for('homepage.homepage'))


@landing_blueprint.route('/feedback')
def feedback_page():
    return render_template('feedback.html')

@landing_blueprint.route('/mentor')
def mentor_page():
    """Serves the AI Mentor chat page."""
    log_visit(page="mentor.html") 
    return render_template('mentor.html')

@landing_blueprint.route('/feedback', methods=['POST'])
def submit_feedback():
    content = request.form.get('feedback_content', '').strip()
    if not content:
        flash('Please enter your feedback before submitting.')
        return redirect(url_for('homepage.feedback_page'))

    user_id = None
    user_uuid = request.cookies.get('tracking_id')
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user_id = user.id

    feedback = Feedback(content=content, user_id=user_id)
    db.session.add(feedback)
    db.session.commit()

    flash('Thank you for your feedback! We really appreciate it.')
    return redirect(url_for('homepage.feedback_page'))