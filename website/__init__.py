import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv



from .consts import (
    DASHBOARD_DEFAULT_NAME,
    PREFIX,
    ROADMAP_DEFAULT_NAME,
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    FALLBACK_SECRET_KEY,
    FALLBACK_SQLALCHEMY_DATABASE_URI,
    CLOUD,
    DATABASE_URL,
    POSTGRES_SQL,
    POSTGRES_SQL_DEPLOYED
)

db = SQLAlchemy()

load_dotenv()


def create_app():
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
        print("Warning: SQLALCHEMY_DATABASE_URI not set in environment. Using fallback value.")
        # Build an absolute path to the local SQLite database to avoid
        # "unable to open database file" errors that can happen when the
        # working directory is different from the project root.
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        instance_dir = os.path.join(project_root, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "testing.db")
        app.config[SQLALCHEMY_DATABASE_URI] = f"sqlite:///{db_path}"

    # Keep the SQLAlchemy option as a boolean-like environment value if present.
    app.config[SQLALCHEMY_TRACK_MODIFICATIONS] = os.getenv(
        SQLALCHEMY_TRACK_MODIFICATIONS
    )

    db.init_app(app)

    with app.app_context():
        from .models.tracking import User, Visit, Action

        from .views import dashboard_blueprint, landing_blueprint, roadmap_blueprint

        app.register_blueprint(dashboard_blueprint, url_prefix=PREFIX + DASHBOARD_DEFAULT_NAME)
        app.register_blueprint(landing_blueprint, url_prefix=PREFIX)
        app.register_blueprint(roadmap_blueprint, url_prefix=PREFIX + ROADMAP_DEFAULT_NAME)

        db.create_all()  

    return app
