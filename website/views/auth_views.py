from urllib.parse import urlparse

from flask import Blueprint, redirect, render_template, request, session, url_for

from authlib.integrations.flask_client import OAuth
from flask_login import login_required, login_user, logout_user
from website.models.temp_user import TempUser
import os

from website import db

from website.models.user import User


from website.consts import (
    AUTH_BASE,
    AUTHORIZE_BASE,
    DOT_PREFIX,
    GOOGLE_USER_EMAIL,
    GOOGLE_USER_FAMILY_NAME,
    GOOGLE_USER_GIVEN_NAME,
    GOOGLE_USER_INFO_API,
    GOOGLE_USER_PICTURE,
    LOGIN_BASE,
    LOGIN_CANCEL,
    LOGIN_GOOGLE_START,
    LOGOUT_BASE,
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

POST_OAUTH_NEXT_KEY = "post_oauth_next"


def _safe_next_url(next_url: str | None) -> str | None:
    """Allow only same-origin paths (Flask-Login may pass a full URL in ?next=)."""
    if not next_url or not isinstance(next_url, str):
        return None
    next_url = next_url.strip()
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        req_netloc = urlparse(request.host_url).netloc
        if parsed.netloc != req_netloc:
            return None
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return path if path.startswith("/") and not path.startswith("//") else None
    if not next_url.startswith("/") or next_url.startswith("//"):
        return None
    return next_url


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
    """Sign-in page: choose Google or return home without signing in."""
    session.pop(POST_OAUTH_NEXT_KEY, None)
    safe = _safe_next_url(request.args.get("next"))
    if safe:
        session[POST_OAUTH_NEXT_KEY] = safe
    return render_template("sign_in.html")


@auth_blueprint.route(PREFIX + LOGIN_GOOGLE_START)
def google_login():
    """Redirect to Google's OAuth consent screen."""
    # Must match an "Authorized redirect URI" in Google Cloud (e.g. http://127.0.0.1:5000/authorize).
    redirect_uri = url_for(AUTH_BASE + DOT_PREFIX + AUTHORIZE_BASE, _external=True)
    print(f"Redirect URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)


@auth_blueprint.route(PREFIX + LOGIN_CANCEL)
def cancel_login():
    """Leave sign-in flow and discard any pending post-login redirect."""
    session.pop(POST_OAUTH_NEXT_KEY, None)
    return redirect(url_for("homepage.homepage"))


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
    app_user = get_user(google_user[GOOGLE_USER_EMAIL])
    if not app_user:
        app_user = create_new_user(google_user)

    print(app_user)

    login_user(app_user)
    session["user"] = app_user.id


    next_path = session.pop(POST_OAUTH_NEXT_KEY, None)
    if next_path:
        return redirect(next_path)
    return redirect(PREFIX)


@auth_blueprint.route(PREFIX + LOGOUT_BASE)
@login_required
def logout():
    logout_user()
    return redirect(PREFIX)

def create_new_user(user):
    """
    This function exists so in the future, when we add roles and stuff
    we will add the roles here.
    """
    # print(user[GOOGLE_USER_EMAIL])
    # print(os.getenv(DEFAULT_ADMIN_EMAIL))


    new_user = User(
        email=user[GOOGLE_USER_EMAIL],
        first_name=user[GOOGLE_USER_GIVEN_NAME],
        last_name=user[GOOGLE_USER_FAMILY_NAME],
        profile_picture=user[GOOGLE_USER_PICTURE],
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

def get_user(email):
    """
    Checks for existing user by email, if found return said user, else return None
    """
    existing_user = User.query.filter_by(email=email).first()
    return existing_user
