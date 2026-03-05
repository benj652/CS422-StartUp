from flask import Blueprint, render_template

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX

landing_blueprint = Blueprint(LANDING_DEFAULT_NAME, __name__)

@landing_blueprint.route(PREFIX)
def landing():
    return render_template(LANDING_DEFAULT_NAME + HTML_EXTENSION)
