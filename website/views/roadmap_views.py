from flask import Blueprint, render_template, request

from website.consts import (
    CS_DEFAULT_NAME,
    ECON_DEFAULT_NAME,
    HTML_EXTENSION,
    MAJOR_SPECIFIC_FOLDER_NAME,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
)
from website.utils import log_visit

roadmap_blueprint = Blueprint(ROADMAP_DEFAULT_NAME, __name__)


@roadmap_blueprint.route(PREFIX)
def roadmap():
    log_visit(page="roadmap")
    return render_template(ROADMAP_DEFAULT_NAME + HTML_EXTENSION)


@roadmap_blueprint.route(CS_DEFAULT_NAME)
def cs():
    log_visit(page="cs")
    selected_year = request.args.get('year', 'Not chosen')

    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + CS_DEFAULT_NAME + HTML_EXTENSION,
        class_year=selected_year
    )


@roadmap_blueprint.route(ECON_DEFAULT_NAME)
def econ():
    log_visit(page="econ")
    selected_year = request.args.get('year', 'Not chosen')
    
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + ECON_DEFAULT_NAME + HTML_EXTENSION,
        class_year=selected_year
    )
