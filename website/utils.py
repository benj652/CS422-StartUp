import uuid
from . import db
from .models.tracking import User, Visit
from flask import request

def get_or_create_user_id():
    # Check if the user already has a tracking cookie
    user_uuid = request.cookies.get('tracking_id')
    
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            return user.id, None # Return ID and no new cookie needed
    
    # If no cookie or user doesn't exist in DB, create a new one
    new_uuid = str(uuid.uuid4())
    new_user = User(uuid=new_uuid)
    db.session.add(new_user)
    db.session.commit()
    
    return new_user.id, new_uuid # Return new ID and the UUID to be set as cookie


_ONBOARDING_PAGE_BY_VARIANT_KEY = {
    "short": "onboarding_variant_a.html",
    "full": "onboarding_variant_b.html",
}


def count_distinct_users_who_visited_onboarding_variant(variant_key: str) -> int:
    """
    Distinct tracking users who loaded the onboarding page for this A/B arm
    (see log_visit in onboarding_variant_a / onboarding_variant_b), independent
    of User.onboarding_variant stored at form submit.
    """
    page = _ONBOARDING_PAGE_BY_VARIANT_KEY.get((variant_key or "").lower())
    if not page:
        return 0
    n = (
        db.session.query(Visit.user_id)
        .filter(Visit.page == page, Visit.user_id.isnot(None))
        .distinct()
        .count()
    )
    return int(n or 0)


def log_visit(page):
    """Logs the visit and returns the user_id and potential new cookie."""
    user_id, new_uuid = get_or_create_user_id()
    
    visit = Visit(page=page, user_id=user_id)
    db.session.add(visit)
    db.session.commit()
    
    return new_uuid 