
"""Pytest fixtures for the test suite.

These fixtures are intentionally simple and used only in tests; test
files disable some pylint checks where appropriate.
"""

# pylint: disable=import-error,wrong-import-position,redefined-outer-name,broad-exception-caught
import os
import sys
import pytest

# ensure project root is on sys.path so tests can import app
_proj_root = os.path.dirname(os.path.dirname(__file__))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from website import create_app
from website import db

flask_app = create_app()



@pytest.fixture(scope="module")
def app():
    """Provide Flask app object for tests (module scope)."""
    return flask_app


@pytest.fixture
def app_ctx(app):
    """Enter a Flask application context for tests."""
    with app.app_context():
        yield


@pytest.fixture(autouse=True)
def cleanup_db(app_ctx):
    """Automatically clean up database before and after each test."""
    from website.models import Note, CameraGear, LabEquipment, Consumable, User
    
    # Clean up before test
    db.session.rollback()
    try:
        # Delete in reverse order of dependencies
        Note.query.delete()
        CameraGear.query.delete()
        LabEquipment.query.delete()
        Consumable.query.delete()
        User.query.delete()
        db.session.commit()
    except Exception:  # pragma: no cover
        db.session.rollback()
    
    yield
    
    # Clean up after test
    db.session.rollback()
    try:
        Note.query.delete()
        CameraGear.query.delete()
        LabEquipment.query.delete()
        Consumable.query.delete()
        User.query.delete()
        db.session.commit()
    except Exception:  # pragma: no cover
        db.session.rollback()


@pytest.fixture
def patcher():
    """A small patch helper to set module attributes and restore them after the test.

    Usage:
        patcher(module, 'AttribName', replacement)
    """
    originals = []

    def _patch(mod, name, value):
        # store original sentinel
        had = hasattr(mod, name)
        orig = getattr(mod, name) if had else None
        setattr(mod, name, value)
        originals.append((mod, name, had, orig))
        return value

    yield _patch

    # teardown: restore originals in reverse order
    for mod, name, had, orig in reversed(originals):
        if had:
            setattr(mod, name, orig)
        else:
            # best-effort removal; tests should not fail on cleanup errors
            try:
                delattr(mod, name)
            except Exception:  # pragma: no cover - defensive cleanup
                pass
