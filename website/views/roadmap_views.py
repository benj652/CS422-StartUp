import json
import os

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

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'roadmap_data.json')

with open(_DATA_PATH) as _f:
    ROADMAP_DATA = json.load(_f)

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
    year_key = request.args.get('year', '').lower()
    cs_data = ROADMAP_DATA['cs']

    career_goal_key = request.args.get('career_goal', '').lower()
    career_stage_key = request.args.get('career_stage', '').lower()
    priority_key = request.args.get('priority', '').lower()

    year_block = cs_data.get(year_key, cs_data['default'])

    base_block = year_block.get('base', {})
    year_data = {
        'classes': base_block.get('classes', []).copy(),
        'programs': base_block.get('programs', []).copy(),
        'resources': base_block.get('resources', []).copy()
    }
    
    goal_data = year_block.get(career_goal_key, {})
    if goal_data:
        year_data['classes'].extend(goal_data.get('extra_classes', []))
        year_data['programs'].extend(goal_data.get('extra_programs', []))
        year_data['resources'].extend(goal_data.get('extra_resources', []))

    stage_data = year_block.get(career_stage_key, {})
    if stage_data:
        year_data['classes'].extend(stage_data.get('extra_classes', []))
        year_data['programs'].extend(stage_data.get('extra_programs', []))
        year_data['resources'].extend(stage_data.get('extra_resources', []))

    priority_data = year_block.get(priority_key, {})
    if priority_data:
        year_data['classes'].extend(priority_data.get('extra_classes', []))
        year_data['programs'].extend(priority_data.get('extra_programs', []))
        year_data['resources'].extend(priority_data.get('extra_resources', []))

    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + CS_DEFAULT_NAME + HTML_EXTENSION,
        **_profile_context(),
        hero=year_block.get('hero', ''),
        highlight=year_block.get('highlight', ''),
        classes=year_data.get('classes',[]),
        programs=year_data.get('programs', []),
        resources=year_data.get('resources',[]),
    )


@roadmap_blueprint.route(ECON_DEFAULT_NAME)
def econ():
    log_visit(page="econ")
    year_key = request.args.get('year', '').lower()
    econ_data = ROADMAP_DATA['econ']
    career_goal_key = request.args.get('career_goal', '').lower()
    career_stage_key = request.args.get('career_stage', '').lower()
    priority_key = request.args.get('priority', '').lower()

    year_block = econ_data.get(year_key, econ_data['default'])

    base_block = year_block.get('base', {})
    year_data = {
        'classes': base_block.get('classes', []).copy(),
        'programs': base_block.get('programs', []).copy(),
        'resources': base_block.get('resources', []).copy()
    }
    
    goal_data = year_block.get(career_goal_key, {})
    if goal_data:
        year_data['classes'].extend(goal_data.get('extra_classes', []))
        year_data['programs'].extend(goal_data.get('extra_programs', []))
        year_data['resources'].extend(goal_data.get('extra_resources', []))

    stage_data = year_block.get(career_stage_key, {})
    if stage_data:
        year_data['classes'].extend(stage_data.get('extra_classes', []))
        year_data['programs'].extend(stage_data.get('extra_programs', []))
        year_data['resources'].extend(stage_data.get('extra_resources', []))

    priority_data = year_block.get(priority_key, {})
    if priority_data:
        year_data['classes'].extend(priority_data.get('extra_classes', []))
        year_data['programs'].extend(priority_data.get('extra_programs', []))
        year_data['resources'].extend(priority_data.get('extra_resources', []))

    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + ECON_DEFAULT_NAME + HTML_EXTENSION,
        **_profile_context(),
        hero=year_block.get('hero', ''),
        highlight=year_block.get('highlight', ''),
        classes=year_data.get('classes',[]),
        programs=year_data.get('programs', []),
        resources=year_data.get('resources',[]),
        
    )
