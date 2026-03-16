from flask import Blueprint, redirect, render_template, request, url_for

from website.consts import (
    CS_DEFAULT_NAME,
    ECON_DEFAULT_NAME,
    HTML_EXTENSION,
    LANDING_DEFAULT_NAME,
    MAJOR_SPECIFIC_FOLDER_NAME,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
)
from website.utils import log_visit

roadmap_blueprint = Blueprint(ROADMAP_DEFAULT_NAME, __name__)

CAREER_GOAL_LABELS = {
    'software_engineer': 'Software Engineer',
    'data_science': 'Data Scientist / Analyst',
    'product_manager': 'Product Manager',
    'finance': 'Finance / Banking',
    'consulting': 'Consulting',
    'exploring': 'Still Exploring',
}

CAREER_STAGE_LABELS = {
    'no_internships': 'No internships yet',
    'applying': 'Currently applying',
    'has_internship': 'Had 1+ internship',
    'has_offer': 'Have a full-time offer',
}

PRIORITY_LABELS = {
    'classes': 'Finding the right classes',
    'internship': 'Landing an internship',
    'projects': 'Building projects',
    'networking': 'Networking & recruiting',
}


def _profile_context():
    return {
        'class_year': request.args.get('year', ''),
        'career_goal': CAREER_GOAL_LABELS.get(request.args.get('career_goal', ''), ''),
        'career_stage': CAREER_STAGE_LABELS.get(request.args.get('career_stage', ''), ''),
        'priority': PRIORITY_LABELS.get(request.args.get('priority', ''), ''),
    }


@roadmap_blueprint.route(PREFIX)
def roadmap():
    return redirect(url_for(LANDING_DEFAULT_NAME + '.onboarding'))


@roadmap_blueprint.route(CS_DEFAULT_NAME)
def cs():
    log_visit(page="cs")
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + CS_DEFAULT_NAME + HTML_EXTENSION,
        **_profile_context()
    )


@roadmap_blueprint.route(ECON_DEFAULT_NAME)
def econ():
    log_visit(page="econ")
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + ECON_DEFAULT_NAME + HTML_EXTENSION,
        **_profile_context()
    )
