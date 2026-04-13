import random

from flask import (
    Blueprint, flash, jsonify, make_response, redirect,
    render_template, request, url_for,
)

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..models.tracking import Action, Feedback, User, db
from ..onboarding_config import QUESTIONS, QUESTIONS_SHORT
from ..utils import log_visit

# A/B: which onboarding length the user sees
ONBOARDING_AB_COOKIE = "onboarding_ab"
_ONBOARDING_AB_MAX_AGE = 30 * 24 * 60 * 60


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

def _render_onboarding(*, questions, variant: str, ob_intro_sub: str):
    return render_template(
        "onboarding.html",
        questions=questions,
        onboarding_variant=variant,
        ob_intro_sub=ob_intro_sub,
    )


@landing_blueprint.route("/onboarding")
def onboarding():
    assigned = request.cookies.get(ONBOARDING_AB_COOKIE)
    if assigned not in ("variantA", "variantB"):
        assigned = random.choice(["variantA", "variantB"])
        target = (
            "homepage.onboarding_variant_a"
            if assigned == "variantA"
            else "homepage.onboarding_variant_b"
        )
        response = make_response(redirect(url_for(target)))
        response.set_cookie(
            ONBOARDING_AB_COOKIE, assigned, max_age=_ONBOARDING_AB_MAX_AGE
        )
        return response
    if assigned == "variantA":
        return redirect(url_for("homepage.onboarding_variant_a"))
    return redirect(url_for("homepage.onboarding_variant_b"))


@landing_blueprint.route("/onboarding/variantA")
def onboarding_variant_a():
    log_visit(page="onboarding_variant_a.html")
    return _render_onboarding(
        questions=QUESTIONS_SHORT,
        variant="short",
        ob_intro_sub="Two quick questions to get your roadmap.",
    )


@landing_blueprint.route("/onboarding/variantB")
def onboarding_variant_b():
    log_visit(page="onboarding_variant_b.html")
    return _render_onboarding(
        questions=QUESTIONS,
        variant="full",
        ob_intro_sub="Five quick questions to personalise your path.",
    )


@landing_blueprint.route('/submit-info', methods=['POST'])
def submit_info():
    class_year = request.form.get('class_year')
    major = request.form.get('major')
    variant = (request.form.get('onboarding_variant') or 'full').lower()
    if variant == 'short':
        career_goal = None
        career_stage = None
        priority = None
    else:
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

            params: dict = {'year': class_year}
            if career_goal:
                params['career_goal'] = career_goal
            if career_stage:
                params['career_stage'] = career_stage
            if priority:
                params['priority'] = priority
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
    print("Feedback ID:", feedback.id)

    flash('Thank you for your feedback! We really appreciate it.')
    return redirect(url_for('homepage.feedback_page'))

@landing_blueprint.route('/roadmap_dashboard')
def onboarding_tracker():
    return render_template('roadmap_dashboard.html')