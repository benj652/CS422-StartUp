"""Flask application factory and database setup."""

import os

from dotenv import load_dotenv
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_login import LoginManager


from .consts import (
    AUTH_BASE,
    CLOUD,
    DASHBOARD_DEFAULT_NAME,
    DATABASE_URL,
    FALLBACK_SECRET_KEY,
    POSTGRES_SQL,
    POSTGRES_SQL_DEPLOYED,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    FALLBACK_SECRET_KEY,
    CLOUD,
    DATABASE_URL,
    POSTGRES_SQL,
    POSTGRES_SQL_DEPLOYED,
)

db = SQLAlchemy()


load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    app.secret_key = os.getenv(SECRET_KEY)

    if not app.secret_key:
        print("Warning: SECRET_KEY not set in environment. Using fallback value.")
        app.secret_key = FALLBACK_SECRET_KEY

    if os.environ.get(CLOUD):
        db_url = os.environ.get(DATABASE_URL)
        if db_url and db_url.startswith(POSTGRES_SQL):
            db_url = db_url.replace(POSTGRES_SQL, POSTGRES_SQL_DEPLOYED, 1)
        app.config[SQLALCHEMY_DATABASE_URI] = db_url
    else:
        app.config[SQLALCHEMY_DATABASE_URI] = os.getenv(SQLALCHEMY_DATABASE_URI)

    if not app.config[SQLALCHEMY_DATABASE_URI]:
        print(
            # Build an absolute path to the local SQLite database to avoid
            # "unable to open database file" errors that can happen when the
            # working directory is different from the project root.
            "Warning: SQLALCHEMY_DATABASE_URI not set in environment. "
            "Using fallback value."
        )
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)
        )
        instance_dir = os.path.join(project_root, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "testing.db")
        app.config[SQLALCHEMY_DATABASE_URI] = f"sqlite:///{db_path}"

    app.config[SQLALCHEMY_TRACK_MODIFICATIONS] = os.getenv(
        SQLALCHEMY_TRACK_MODIFICATIONS
    )

    # Initialize the LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = PREFIX + AUTH_BASE
    login_manager.login_message = None

    db.init_app(app)

    from .views import (
        auth_blueprint,
        dashboard_blueprint,
        landing_blueprint,
        roadmap_blueprint,
    )

    app.register_blueprint(
        dashboard_blueprint, url_prefix=PREFIX + DASHBOARD_DEFAULT_NAME
    )
    app.register_blueprint(landing_blueprint, url_prefix=PREFIX)
    app.register_blueprint(roadmap_blueprint, url_prefix=PREFIX + ROADMAP_DEFAULT_NAME)
    app.register_blueprint(auth_blueprint, url_prefix=PREFIX + AUTH_BASE)


    @app.errorhandler(404)
    def page_not_found(e):
        """Redirect to the configured not-found route.

        The argument is provided by Flask's error handler API but is not
        used here.
        """
        # pylint: disable=unused-argument
        return redirect("/")
    @app.errorhandler(403)
    def not_authorized(e):
        """Redirect to the configured not-found route.

        The argument is provided by Flask's error handler API but is not
        used here.
        """
        # pylint: disable=unused-argument
        return redirect("/")

    from website.models.tracking import (
        User,
    )
    with app.app_context():
        db.create_all()


    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by ID for Flask-Login.

        Since we are not persisting users in the database, this function
        will create a temporary user object with the given user_id.
        """

        return User.query.get(user_id)

    from website.views.auth_views import init_oauth

    init_oauth(app)

    # app.register_blueprint(
    #     dashboard_blueprint,
    #     url_prefix=PREFIX + DASHBOARD_DEFAULT_NAME,
    # )
    # app.register_blueprint(landing_blueprint, url_prefix=PREFIX)
    # app.register_blueprint(
    #     roadmap_blueprint,
    #     url_prefix=PREFIX + ROADMAP_DEFAULT_NAME,
    # )

    return app
