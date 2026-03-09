from flask import Blueprint, render_template

from ..consts import HTML_EXTENSION, LANDING_DEFAULT_NAME, PREFIX
from ..utils import log_visit
from flask import request, make_response

landing_blueprint = Blueprint(LANDING_DEFAULT_NAME, __name__)


@landing_blueprint.route(PREFIX)
def landing():
    new_uuid = log_visit(page="homepage.html")
    response = make_response(render_template(LANDING_DEFAULT_NAME + HTML_EXTENSION))
    
    if new_uuid:
        # Set cookie to expire in 30 days
        response.set_cookie('tracking_id', new_uuid, max_age=30*24*60*60)
    
    return response
