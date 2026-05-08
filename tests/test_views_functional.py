# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,import-outside-toplevel,too-many-lines,unused-argument
import json
from types import SimpleNamespace

import pytest

from website import db
from website.models.tracking import User as TrackingUser, Action, Visit, Feedback
from website.models.user import User, WishlistItem


def login_user_in_client(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


class TestLandingAndRoadmapFunctional:
    def test_homepage_sets_tracking_cookie_and_creates_visit(self, app, app_ctx):
        with app.test_client() as client:
            rv = client.get("/")
            assert rv.status_code == 200
            set_cookie = rv.headers.get("Set-Cookie", "")
            assert "tracking_id=" in set_cookie

            visits = Visit.query.filter_by(page="homepage.html").all()
            assert visits, "Expected at least one Visit row for homepage"

    def test_onboarding_assigns_ab_cookie_and_redirects(self, app, app_ctx):
        with app.test_client() as client:
            rv = client.get("/onboarding")
            assert rv.status_code in (302, 301)
            set_cookie = rv.headers.get("Set-Cookie", "")
            assert "onboarding_ab=" in set_cookie

    def test_onboarding_variant_pages_return_200(self, app, app_ctx):
        with app.test_client() as client:
            rv_a = client.get("/onboarding/variantA")
            assert rv_a.status_code == 200
            rv_b = client.get("/onboarding/variantB")
            assert rv_b.status_code == 200

    def test_track_action_requires_json(self, app, app_ctx):
        with app.test_client() as client:
            rv = client.post("/track-action", data="notjson", content_type="text/plain")
            assert rv.status_code == 400

    def test_track_action_records_action_when_user_cookie(self, app, app_ctx):
        tuser = TrackingUser(uuid="track-test-1")
        db.session.add(tuser)
        db.session.commit()

        with app.test_client() as client:
            client.set_cookie(key="tracking_id", value="track-test-1")

            payload = {"atype": "roadmap_link_click", "detail": {"foo": "bar"}}
            rv = client.post("/track-action", json=payload)

            assert rv.status_code == 200

            a = Action.query.filter_by(atype="roadmap_link_click").first()
            assert a is not None
            assert a.detail and a.detail.get("foo") == "bar"

    def test_submit_info_creates_core_action_and_redirects(self, app, app_ctx):
        tuser = TrackingUser(uuid="track-test-2")
        db.session.add(tuser)
        db.session.commit()

        with app.test_client() as client:
            client.set_cookie(key="tracking_id", value="track-test-2")

            data = {
                "class_year": "2026",
                "major": "cs",
                "onboarding_variant": "full",
                "career_goal": "research",
                "career_stage": "early",
                "priority": "high",
            }

            rv = client.post("/submit-info", data=data, follow_redirects=False)
            assert rv.status_code in (302, 301)

            a = Action.query.filter_by(atype="roadmap_submit").first()
            assert a is not None

    def test_feedback_post_creates_feedback(self, app, app_ctx):
        tuser = TrackingUser(uuid="track-test-3")
        db.session.add(tuser)
        db.session.commit()

        with app.test_client() as client:
            client.set_cookie(key="tracking_id", value="track-test-3")

            rv = client.post("/feedback", data={"feedback_content": "Great site!"})
            assert rv.status_code in (302, 301)

            f = Feedback.query.filter_by(content="Great site!").first()
            assert f is not None

    def test_wishlist_save_requires_auth(self, app, app_ctx):
        with app.test_client() as client:
            rv = client.post("/wishlist/items/from-roadmap", json={})
            assert rv.status_code == 401

    def test_wishlist_save_creates_item_when_logged_in(self, app, app_ctx):
        app_user = User(first_name="Test", last_name="User", email="tuser@example.com")
        db.session.add(app_user)
        db.session.commit()

        with app.test_client() as client:
            login_user_in_client(client, app_user)

            payload = {
                "roadmap_item_id": "item-123",
                "title": "Do something",
                "checked": True,
            }

            rv = client.post("/wishlist/items/from-roadmap", json=payload)
            assert rv.status_code == 200

            item = WishlistItem.query.filter_by(
                roadmap_item_id="item-123", user_id=app_user.id
            ).first()

            assert item is not None

    def test_export_roadmap_metrics_csv_empty(self, app, app_ctx):
        with app.test_client() as client:
            rv = client.get("/dashboard/export-roadmap-metrics.csv")
            assert rv.status_code == 200
            assert "text/csv" in rv.headers.get("Content-Type", "")

            data = rv.get_data(as_text=True)
            assert "user_id,variant_letter" in data
