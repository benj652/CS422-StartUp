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

@landing_blueprint.route('/onboarding')
def onboarding():
    log_visit(page="onboarding.html")
    return render_template('onboarding.html')


@landing_blueprint.route('/submit-info', methods=['POST'])
def submit_info():
    class_year = request.form.get('class_year')
    major = request.form.get('major')
    career_goal = request.form.get('career_goal')
    career_stage = request.form.get('career_stage')
    priority = request.form.get('priority')
    user_uuid = request.cookies.get('tracking_id')

    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user.class_year = class_year
            user.major = major
            user.career_goal = career_goal
            user.career_stage = career_stage
            user.priority = priority

            core_action = Action(atype='roadmap_submit', user_id=user.id)
            db.session.add(core_action)
            db.session.commit()

            params = dict(
                year=class_year,
                career_goal=career_goal,
                career_stage=career_stage,
                priority=priority,
            )
            if major == 'cs':
                return redirect(url_for('roadmap.cs', **params))
            elif major == 'econ':
                return redirect(url_for('roadmap.econ', **params))

    return redirect(url_for('homepage.homepage'))


@landing_blueprint.route('/feedback')
def feedback_page():
    log_visit(page="feedback.html")
    return render_template('feedback.html')


@landing_blueprint.route('/privacy')
def privacy():
    return render_template('privacy.html')


@landing_blueprint.route('/cookies')
def cookie_policy():
    return render_template('cookies.html')


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