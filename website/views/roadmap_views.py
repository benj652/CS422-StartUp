from flask import Blueprint, render_template

from website.consts import (
    CS_DEFAULT_NAME,
    ECON_DEFAULT_NAME,
    HTML_EXTENSION,
    MAJOR_SPECIFIC_FOLDER_NAME,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
)

roadmap_blueprint = Blueprint(ROADMAP_DEFAULT_NAME, __name__)


@roadmap_blueprint.route(PREFIX)
def roadmap():
    return render_template(ROADMAP_DEFAULT_NAME + HTML_EXTENSION)


@roadmap_blueprint.route(CS_DEFAULT_NAME)
def cs():
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + CS_DEFAULT_NAME + HTML_EXTENSION
    )


@roadmap_blueprint.route(ECON_DEFAULT_NAME)
def econ():
    return render_template(
        MAJOR_SPECIFIC_FOLDER_NAME + ECON_DEFAULT_NAME + HTML_EXTENSION
    )
