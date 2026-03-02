from flask import Blueprint, render_template

from website.consts import HTML_EXTENSION, PREFIX, ROADMAP_DEFAULT_NAME

roadmap_blueprint = Blueprint(ROADMAP_DEFAULT_NAME, __name__)

@roadmap_blueprint.route(PREFIX)
def roadmap():
    return render_template(ROADMAP_DEFAULT_NAME + HTML_EXTENSION)
