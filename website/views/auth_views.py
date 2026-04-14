from flask import Blueprint, redirect, session, url_for

from authlib.integrations.flask_client import OAuth
from flask_login import login_required, login_user, logout_user
from website.models.temp_user import TempUser
import os


from website.consts import (
    AUTH_BASE,
    AUTHORIZE_BASE,
    DOT_PREFIX,
    GOOGLE_USER_INFO_API,
    LOGIN_BASE,
    LOGOUT_BASE,
    ONBOARDING_BASE,
    PREFIX,
    OAUTH_NAME,
    SERVER_METADATA_URL,
    CLIENT_KWARGS_KEY,
    CLIENT_KWARGS_ITEMS,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)


oauth = OAuth()
google = None


def init_oauth(app):
    """Initialize OAuth and register Google provider."""
    global google
    oauth.init_app(app)

    google = oauth.register(
        name=OAUTH_NAME,
        server_metadata_url=SERVER_METADATA_URL,
        client_id=os.getenv(GOOGLE_CLIENT_ID),
        client_secret=os.getenv(GOOGLE_CLIENT_SECRET),
        client_kwargs={CLIENT_KWARGS_KEY: CLIENT_KWARGS_ITEMS},
    )


auth_blueprint = Blueprint(AUTH_BASE, __name__)


@auth_blueprint.route(PREFIX + LOGIN_BASE)
def login():
    """Start the OAuth login flow by redirecting to Google's authorize URL."""
    redirect_uri = url_for(AUTH_BASE + DOT_PREFIX + AUTHORIZE_BASE, _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_blueprint.route(PREFIX + AUTHORIZE_BASE)
def authorize():
    """
    Authorize user and fetch user info from Google

    the user item is in the following format:
    {
        'id': '114544450990536914219',
        'email': 'bmjaff26@colby.edu',
        'verified_email': True,
        'name': 'Benjamin Jaffe',
        'given_name': 'Benjamin',
        'family_name': 'Jaffe',
        'picture': 'https://lh3.googleusercontent.com/a/ACg8ocJwc-igE1-1TWV732HsBwAAu8kC9JpfbLsPOGVQD1aO2Cp_9w=s96-c',
        'hd': 'colby.edu'
    }
    """
    token = google.authorize_access_token()
    resp = google.get(GOOGLE_USER_INFO_API, token=token)
    google_user = resp.json()

    # Create a TempUser instance from the Google user info
    user = TempUser(
        user_id=google_user["id"], email=google_user["email"], name=google_user["name"]
    )

    login_user(user)
    return redirect(PREFIX + ONBOARDING_BASE)


@auth_blueprint.route(PREFIX + LOGOUT_BASE)
@login_required
def logout():
    logout_user()
    return redirect(PREFIX)
