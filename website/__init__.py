import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from .views import dashboard_blueprint, landing_blueprint, roadmap_blueprint

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
        app.config[SQLALCHEMY_DATABASE_URI] = FALLBACK_SQLALCHEMY_DATABASE_URI

    # Keep the SQLAlchemy option as a boolean-like environment value if present.
    app.config[SQLALCHEMY_TRACK_MODIFICATIONS] = os.getenv(
        SQLALCHEMY_TRACK_MODIFICATIONS
    )

    db.init_app(app)

    app.register_blueprint(dashboard_blueprint, url_prefix=PREFIX + DASHBOARD_DEFAULT_NAME)
    app.register_blueprint(landing_blueprint, url_prefix=PREFIX)
    app.register_blueprint(roadmap_blueprint, url_prefix=PREFIX + ROADMAP_DEFAULT_NAME)

    with app.app_context():
        db.create_all()  

    return app
