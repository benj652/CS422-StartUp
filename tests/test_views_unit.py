import pytest
from types import SimpleNamespace

from website.views import auth_views, roadmap_views, landing_views, dashboard_views


# ---------------------------
# FIX: alias missing fixture
# ---------------------------
@pytest.fixture
def _app_ctx(app_ctx):
    return app_ctx


# ---------------------------
# roadmap cache key
# ---------------------------
def test_cache_key_is_deterministic():
    p = {
        "major": "cs",
        "year": "senior",
        "career_goal": "",
        "career_stage": "",
        "priority": "",
    }
    k1 = roadmap_views._cache_key(p)
    k2 = roadmap_views._cache_key(p.copy())
    assert k1.startswith("roadmap_")
    assert k1 == k2


# ---------------------------
# admin password validation
# ---------------------------
def test_admin_password_is_valid_true_and_false():
    good = "secretpw"
    bad = "wrong"

    assert landing_views._admin_password_is_valid(provided=good, expected=good) is True
    assert landing_views._admin_password_is_valid(provided=bad, expected=good) is False
    assert landing_views._admin_password_is_valid(provided="", expected=good) is False
    assert landing_views._admin_password_is_valid(provided=good, expected="") is False


# ---------------------------
# mentor profile
# ---------------------------
def test_mentor_profile_context_and_llm_profile():
    ctx = landing_views._mentor_profile_context(None)
    assert ctx["profile_class_year"] == "Not set yet"

    llm = landing_views._mentor_llm_profile(None)
    assert llm["class_year"] == ""

    tu = SimpleNamespace(
        class_year="2026",
        major="cs",
        career_goal="software_engineer",
        career_stage="no_internships",
        onboarding_variant="full",
    )

    ctx2 = landing_views._mentor_profile_context(tu)
    assert ctx2["profile_class_year"] == "2026"

    llm2 = landing_views._mentor_llm_profile(tu)
    assert llm2["class_year"] == "2026"
    assert llm2["major"] == "cs"


# ---------------------------
# dashboard helpers
# ---------------------------
def test_sum_roadmap_time_seconds_from_details_handles_various_values():
    good = SimpleNamespace(atype="roadmap_time_on_page", detail={"seconds": "30"})
    int_sec = SimpleNamespace(atype="roadmap_time_on_page", detail={"seconds": 45})
    missing = SimpleNamespace(atype="roadmap_time_on_page", detail={"foo": "bar"})
    not_dict = SimpleNamespace(atype="roadmap_time_on_page", detail="string")
    other_action = SimpleNamespace(atype="roadmap_link_click", detail={"seconds": 100})

    total = dashboard_views._sum_roadmap_time_seconds_from_details(
        [good, int_sec, missing, not_dict, other_action]
    )
    assert total == 75


def test_label_for_value_with_mappings():
    mapping = {"x": "Label X"}

    assert dashboard_views._label_for_value(mapping, "x") == "Label X"
    assert dashboard_views._label_for_value(mapping, None) == "Not answered"
    assert dashboard_views._label_for_value(mapping, "") == "Not answered"
    assert dashboard_views._label_for_value(mapping, "unknown") == "unknown"
